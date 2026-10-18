from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapters import validate_c3_path
from .models import Claim, CognitiveStatus, FactualStatus, VerifiedClaim


@dataclass(frozen=True)
class C4Config:
    """Pilot rules; replace with approved project rules during calibration."""

    mastery_threshold: float = 0.7
    uncertainty_threshold: float = 0.25
    max_rewrite_attempts: int = 3
    default_bloom_ceiling: int = 2
    mastered_bloom_ceiling: int = 3


@dataclass
class C4Result:
    learner_id: str
    target: str
    verified_path: bool
    original_explanation: str
    final_explanation: str
    initial_claims: list[VerifiedClaim]
    claims: list[VerifiedClaim]
    rewrite_attempts: int
    unresolved_claims: list[str]

    def to_dict(self) -> dict:
        return {
            "learner_id": self.learner_id,
            "target": self.target,
            "verified_path": self.verified_path,
            "original_explanation": self.original_explanation,
            "final_explanation": self.final_explanation,
            "initial_claims": [claim.to_dict() for claim in self.initial_claims],
            "claims": [claim.to_dict() for claim in self.claims],
            "rewrite_attempts": self.rewrite_attempts,
            "unresolved_claims": self.unresolved_claims,
        }


class C4Pipeline:
    """Deterministic C4 proof of concept using C3-compatible JSON inputs."""

    def __init__(self, knowledge_graph: dict[str, Any], config: C4Config | None = None):
        self.kg = knowledge_graph
        self.config = config or C4Config()

    @classmethod
    def from_files(
        cls, knowledge_graph_path: str | Path, config: C4Config | None = None
    ) -> "C4Pipeline":
        with Path(knowledge_graph_path).open(encoding="utf-8") as handle:
            return cls(json.load(handle), config)

    def run(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        explanation: str,
    ) -> C4Result:
        validate_c3_path(c3_path)
        if not c3_path.get("verified", False):
            raise ValueError("C4 accepts only verified paths from C3")

        current_text = explanation.strip()
        attempts = 0
        initial_claims = self._verify_all(current_text, c3_path, learner_state)
        claims = initial_claims
        while any(not claim.accepted for claim in claims) and attempts < self.config.max_rewrite_attempts:
            current_text = self._rewrite(current_text, claims, c3_path, learner_state)
            attempts += 1
            claims = self._verify_all(current_text, c3_path, learner_state)

        unresolved = [claim.claim.claim_id for claim in claims if not claim.accepted]
        return C4Result(
            learner_id=c3_path["learner_id"],
            target=c3_path["target"],
            verified_path=True,
            original_explanation=explanation,
            final_explanation=current_text,
            initial_claims=initial_claims,
            claims=claims,
            rewrite_attempts=attempts,
            unresolved_claims=unresolved,
        )

    def _verify_all(
        self, explanation: str, c3_path: dict[str, Any], learner_state: dict[str, Any]
    ) -> list[VerifiedClaim]:
        return [
            self._verify_claim(claim, c3_path, learner_state)
            for claim in self._decompose(explanation)
        ]

    def _decompose(self, explanation: str) -> list[Claim]:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", explanation) if part.strip()]
        claims = []
        for index, sentence in enumerate(sentences, 1):
            concept_ids = tuple(
                concept_id
                for concept_id, value in self.kg.get("concepts", {}).items()
                if self._contains_term(sentence, value.get("name", concept_id))
                or concept_id.replace("_", " ") in sentence.lower()
            )
            claims.append(
                Claim(
                    claim_id=f"claim-{index}",
                    text=sentence,
                    concept_ids=concept_ids,
                    estimated_bloom_level=self._estimate_bloom(sentence),
                )
            )
        return claims

    def _verify_claim(
        self, claim: Claim, c3_path: dict[str, Any], learner_state: dict[str, Any]
    ) -> VerifiedClaim:
        factual_status, evidence = self._check_factual(claim)
        cognitive_status = self._check_cognitive(claim, c3_path, learner_state)
        violations: list[str] = []
        if factual_status == "CONTRADICTED":
            violations.append("CONTRADICTED_CLAIM")
        elif factual_status == "UNSUPPORTED":
            violations.append("UNSUPPORTED_CLAIM")
        if cognitive_status == "BLOOM_MISMATCH":
            violations.append("BLOOM_MISMATCH")
        elif cognitive_status == "UNMASTERED_PREREQUISITE":
            violations.append("UNMASTERED_PREREQUISITE")
        confidence = "HIGH" if evidence and not violations else "MEDIUM" if evidence else "LOW"
        return VerifiedClaim(claim, factual_status, cognitive_status, evidence, violations, confidence)

    def _check_factual(self, claim: Claim) -> tuple[FactualStatus, list[str]]:
        facts = []
        for concept_id in claim.concept_ids:
            facts.extend(self.kg.get("concepts", {}).get(concept_id, {}).get("facts", []))
        normalized_claim = self._normalize(claim.text)
        for fact in facts:
            normalized_fact = self._normalize(fact)
            if normalized_fact in normalized_claim or normalized_claim in normalized_fact:
                return "ENTAILED", [fact]
        contradiction = next(
            (
                fact
                for fact in facts
                if self._normalize(f"not {fact}") in normalized_claim
            ),
            None,
        )
        if contradiction:
            return "CONTRADICTED", [contradiction]
        return "UNSUPPORTED", []

    def _check_cognitive(
        self, claim: Claim, c3_path: dict[str, Any], learner_state: dict[str, Any]
    ) -> CognitiveStatus:
        ceiling = self._bloom_ceiling(c3_path, learner_state)
        if claim.estimated_bloom_level and claim.estimated_bloom_level > ceiling:
            return "BLOOM_MISMATCH"
        mastery = learner_state.get("mastery", {})
        for concept_id in claim.concept_ids:
            prerequisites = self.kg.get("concepts", {}).get(concept_id, {}).get("prerequisites", [])
            if any(float(mastery.get(prerequisite, 0.0)) < self.config.mastery_threshold
                   for prerequisite in prerequisites):
                return "UNMASTERED_PREREQUISITE"
        return "APPROPRIATE"

    def _bloom_ceiling(self, c3_path: dict[str, Any], learner_state: dict[str, Any]) -> int:
        target = c3_path["target"]
        prerequisites = self.kg.get("concepts", {}).get(target, {}).get("prerequisites", [])
        mastery = learner_state.get("mastery", {})
        uncertainty = learner_state.get("uncertainty", {})
        ready = all(
            float(mastery.get(prerequisite, 0.0)) >= self.config.mastery_threshold
            and float(uncertainty.get(prerequisite, 0.5)) < self.config.uncertainty_threshold
            for prerequisite in prerequisites
        )
        return self.config.mastered_bloom_ceiling if ready else self.config.default_bloom_ceiling

    def _rewrite(
        self,
        explanation: str,
        claims: list[VerifiedClaim],
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
    ) -> str:
        replacements = {}
        for verified in claims:
            if verified.accepted:
                continue
            replacement = self._safe_rewrite(verified, c3_path)
            replacements[verified.claim.text] = replacement
            verified.rewritten_text = replacement
        for original, replacement in replacements.items():
            explanation = explanation.replace(original, replacement, 1)
        return explanation

    def _safe_rewrite(self, verified: VerifiedClaim, c3_path: dict[str, Any]) -> str:
        target = self.kg.get("concepts", {}).get(c3_path["target"], {})
        if "UNSUPPORTED_CLAIM" in verified.violations or "CONTRADICTED_CLAIM" in verified.violations:
            facts = target.get("facts", [])
            if facts:
                return facts[0]
        target_name = target.get("name", c3_path["target"])
        return f"{target_name} requires the verified learning path and its prerequisites."

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()

    @staticmethod
    def _contains_term(sentence: str, term: str) -> bool:
        return re.search(rf"\b{re.escape(term.lower())}\b", sentence.lower()) is not None

    @staticmethod
    def _estimate_bloom(sentence: str) -> int:
        lowered = sentence.lower()
        if any(word in lowered for word in ("design", "create", "evaluate")):
            return 6
        if any(word in lowered for word in ("analyze", "compare", "analyse")):
            return 4
        if any(word in lowered for word in ("explain", "describe", "why")):
            return 2
        return 1

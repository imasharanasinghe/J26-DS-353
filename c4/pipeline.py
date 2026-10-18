from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .adapters import validate_c3_path
from .metrics import summarize
from .models import (
    Claim,
    CognitiveStatus,
    FactualStatus,
    RewriteStep,
    VerifiedClaim,
)

STOPWORDS = frozenset(
    "a an the is are was were of to in on by at and or it its with for as be can".split()
)
NEGATIONS = frozenset({"not", "never", "no", "cannot"})

# Verb cues for the pilot Bloom estimator (revised taxonomy level per cue).
BLOOM_CUES: tuple[tuple[int, tuple[str, ...]], ...] = (
    (6, ("design", "create", "construct", "develop")),
    (5, ("evaluate", "justify", "critique", "assess")),
    (4, ("analyze", "analyse", "compare", "differentiate", "examine")),
    (3, ("implement", "apply", "solve", "compute")),
    (2, ("explain", "describe", "why", "summarize")),
)


@dataclass(frozen=True)
class C4Config:
    """Pilot rules; replace with approved project rules during calibration.

    A prerequisite counts as mastered when ``mastery >= mastery_threshold`` and
    ``uncertainty <= uncertainty_threshold``. Mastery within ``threshold_margin``
    of the threshold, uncertainty above the threshold, or missing learner
    history is INCONCLUSIVE rather than silently accepted or rejected.
    """

    mastery_threshold: float = 0.7
    uncertainty_threshold: float = 0.25
    threshold_margin: float = 0.05
    max_rewrite_attempts: int = 3
    default_bloom_ceiling: int = 2
    mastered_bloom_ceiling: int = 3
    entail_similarity: float = 0.6
    contradict_recall: float = 0.75
    check_factual: bool = True
    check_cognitive: bool = True
    rewrite: bool = True


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
    trace: list[RewriteStep] = field(default_factory=list)
    review_first: list[str] = field(default_factory=list)
    latency_s: float = 0.0
    config: dict[str, Any] = field(default_factory=dict)

    @property
    def metrics(self) -> dict[str, Any]:
        return summarize(self)

    def to_dict(self) -> dict:
        return {
            "schema_version": "c4-report/1.0",
            "learner_id": self.learner_id,
            "target": self.target,
            "verified_path": self.verified_path,
            "original_explanation": self.original_explanation,
            "final_explanation": self.final_explanation,
            "initial_claims": [claim.to_dict() for claim in self.initial_claims],
            "claims": [claim.to_dict() for claim in self.claims],
            "rewrite_attempts": self.rewrite_attempts,
            "rewrite_trace": [step.to_dict() for step in self.trace],
            "unresolved_claims": self.unresolved_claims,
            "review_first": self.review_first,
            "metrics": self.metrics,
            "latency_s": round(self.latency_s, 4),
            "config": self.config,
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

    # ------------------------------------------------------------------ run

    def run(
        self,
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
        explanation: str,
    ) -> C4Result:
        validate_c3_path(c3_path)
        if not c3_path.get("verified", False):
            raise ValueError("C4 accepts only verified paths from C3")

        started = time.perf_counter()
        sentences = self._split(explanation)
        initial_claims = self._verify_all(sentences, c3_path, learner_state)
        claims = initial_claims
        trace: list[RewriteStep] = []
        attempts = 0
        while (
            self.config.rewrite
            and any(not claim.accepted for claim in claims)
            and attempts < self.config.max_rewrite_attempts
        ):
            changed = False
            for index, verified in enumerate(claims):
                if verified.accepted:
                    continue
                replacement, strategy = self._rewrite(verified, index, sentences, c3_path, learner_state)
                if replacement == sentences[index]:
                    continue
                trace.append(RewriteStep(
                    attempts + 1, verified.claim.claim_id, tuple(verified.violations),
                    sentences[index], replacement, strategy,
                ))
                verified.rewritten_text = replacement
                sentences[index] = replacement
                changed = True
            if not changed:
                break
            attempts += 1
            claims = self._verify_all(sentences, c3_path, learner_state)

        unresolved = [claim.claim.claim_id for claim in claims if not claim.accepted]
        return C4Result(
            learner_id=c3_path["learner_id"],
            target=c3_path["target"],
            verified_path=True,
            original_explanation=explanation,
            final_explanation=" ".join(item for item in sentences if item),
            initial_claims=initial_claims,
            claims=claims,
            rewrite_attempts=attempts,
            unresolved_claims=unresolved,
            trace=trace,
            review_first=self._review_first(initial_claims, c3_path, learner_state),
            latency_s=time.perf_counter() - started,
            config=asdict(self.config),
        )

    # --------------------------------------------------------- decomposition

    @staticmethod
    def _split(explanation: str) -> list[str]:
        return [part.strip() for part in re.split(r"(?<=[.!?])\s+", explanation.strip()) if part.strip()]

    def _verify_all(
        self, sentences: list[str], c3_path: dict[str, Any], learner_state: dict[str, Any]
    ) -> list[VerifiedClaim]:
        return [
            self._verify_claim(self._build_claim(index, sentence), c3_path, learner_state)
            for index, sentence in enumerate(sentences, 1)
            if sentence
        ]

    def _build_claim(self, index: int, sentence: str) -> Claim:
        return Claim(
            claim_id=f"claim-{index}",
            text=sentence,
            concept_ids=self._mentioned_concepts(sentence),
            estimated_bloom_level=self._estimate_bloom(sentence),
        )

    def _mentioned_concepts(self, sentence: str) -> tuple[str, ...]:
        """Longest-match concept detection so 'binary tree' does not also match 'tree'."""
        tokens = [self._stem(word) for word in re.findall(r"[a-z0-9]+", sentence.lower())]
        concepts = self.kg.get("concepts", {})
        patterns = []
        for concept_id, value in concepts.items():
            for label in {value.get("name", concept_id), concept_id.replace("_", " ")}:
                words = [self._stem(word) for word in re.findall(r"[a-z0-9]+", label.lower())]
                if words:
                    patterns.append((len(words), words, concept_id))
        patterns.sort(key=lambda item: -item[0])
        consumed = [False] * len(tokens)
        found: list[str] = []
        for size, words, concept_id in patterns:
            for start in range(len(tokens) - size + 1):
                span = range(start, start + size)
                if tokens[start:start + size] == words and not any(consumed[i] for i in span):
                    for i in span:
                        consumed[i] = True
                    if concept_id not in found:
                        found.append(concept_id)
        return tuple(sorted(found))

    # ------------------------------------------------------------ verification

    def _verify_claim(
        self, claim: Claim, c3_path: dict[str, Any], learner_state: dict[str, Any]
    ) -> VerifiedClaim:
        factual_status, evidence = self._check_factual(claim, c3_path)
        cognitive_status = self._check_cognitive(claim, c3_path, learner_state)
        violations: list[str] = []
        if self.config.check_factual:
            if factual_status == "CONTRADICTED":
                violations.append("CONTRADICTED_CLAIM")
            elif factual_status == "UNSUPPORTED":
                violations.append("UNSUPPORTED_CLAIM")
        if self.config.check_cognitive:
            if cognitive_status == "BLOOM_MISMATCH":
                violations.append("BLOOM_MISMATCH")
            elif cognitive_status == "UNMASTERED_PREREQUISITE":
                violations.append("UNMASTERED_PREREQUISITE")
            elif cognitive_status == "INCONCLUSIVE":
                violations.append("INCONCLUSIVE_COGNITIVE")
        if self._is_guidance(claim.text, c3_path):
            confidence = "MEDIUM" if not violations else "LOW"
        elif factual_status == "ENTAILED" and cognitive_status == "APPROPRIATE":
            confidence = "HIGH"
        elif evidence:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        return VerifiedClaim(claim, factual_status, cognitive_status, evidence, violations, confidence)

    def _check_factual(
        self, claim: Claim, c3_path: dict[str, Any]
    ) -> tuple[FactualStatus, list[str]]:
        """Rule-based graph-edge mapping: compare content words with graph statements."""
        if self._is_guidance(claim.text, c3_path):
            return "ENTAILED", ["pipeline guidance sentence; asserts no domain fact"]
        concepts = self.kg.get("concepts", {})
        facts: list[str] = []
        known_false: list[str] = []
        for concept_id in claim.concept_ids:
            facts.extend(concepts.get(concept_id, {}).get("facts", []))
            known_false.extend(concepts.get(concept_id, {}).get("known_false", []))
        claim_words = self._content_words(claim.text)
        claim_negated = self._negated(claim.text)

        best_fact, best_score = None, 0.0
        for fact in facts:
            score = self._jaccard(self._content_words(fact), claim_words)
            if score > best_score:
                best_fact, best_score = fact, score

        # A known-false statement only wins when the claim is closer to it than to any
        # true fact (e.g. LIFO vs FIFO differ by one word) and the negation polarity matches.
        for statement in known_false:
            false_words = self._content_words(statement)
            if not false_words or self._negated(statement) != claim_negated:
                continue
            recall = len(false_words & claim_words) / len(false_words)
            if recall >= self.config.contradict_recall and \
                    self._jaccard(false_words, claim_words) > best_score:
                return "CONTRADICTED", [f"contradicts graph misconception: {statement}"]

        if best_fact is not None and best_score >= self.config.entail_similarity:
            if claim_negated and not self._negated(best_fact):
                return "CONTRADICTED", [f"negates graph fact: {best_fact}"]
            return "ENTAILED", [best_fact]
        return "UNSUPPORTED", []

    @staticmethod
    def _negated(text: str) -> bool:
        return bool(set(re.findall(r"[a-z]+", text.lower())) & NEGATIONS)

    @staticmethod
    def _jaccard(left: set[str], right: set[str]) -> float:
        union = left | right
        return len(left & right) / len(union) if union else 0.0

    def _mastery_state(self, concept_id: str, learner_state: dict[str, Any]) -> str:
        mastery = learner_state.get("mastery", {})
        uncertainty = learner_state.get("uncertainty", {})
        if concept_id not in mastery:
            return "UNKNOWN"
        score = float(mastery[concept_id])
        threshold = self.config.mastery_threshold
        if abs(score - threshold) < self.config.threshold_margin:
            return "UNKNOWN"
        if score < threshold:
            return "UNMASTERED"
        if float(uncertainty.get(concept_id, 1.0)) > self.config.uncertainty_threshold:
            return "UNKNOWN"
        return "MASTERED"

    def _check_cognitive(
        self, claim: Claim, c3_path: dict[str, Any], learner_state: dict[str, Any]
    ) -> CognitiveStatus:
        """Bloom ceiling first, then mastery of every non-target concept the claim relies on.

        The current target is exempt: being new to the learner is not a violation.
        """
        if self._is_guidance(claim.text, c3_path):
            return "APPROPRIATE"
        ceiling = self._bloom_ceiling(c3_path, learner_state)
        if claim.estimated_bloom_level and claim.estimated_bloom_level > ceiling:
            return "BLOOM_MISMATCH"
        states = [
            self._mastery_state(concept_id, learner_state)
            for concept_id in claim.concept_ids
            if concept_id != c3_path["target"]
        ]
        if "UNMASTERED" in states:
            return "UNMASTERED_PREREQUISITE"
        if "UNKNOWN" in states:
            return "INCONCLUSIVE"
        return "APPROPRIATE"

    def _bloom_ceiling(self, c3_path: dict[str, Any], learner_state: dict[str, Any]) -> int:
        """Ceiling is raised only when every direct prerequisite of the target is mastered."""
        prerequisites = self.kg.get("concepts", {}).get(c3_path["target"], {}).get("prerequisites", [])
        ready = all(self._mastery_state(item, learner_state) == "MASTERED" for item in prerequisites)
        return self.config.mastered_bloom_ceiling if ready else self.config.default_bloom_ceiling

    # ----------------------------------------------------------------- repair

    def _rewrite(
        self,
        verified: VerifiedClaim,
        index: int,
        sentences: list[str],
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
    ) -> tuple[str, str]:
        """Targeted replacement for one violating sentence.

        Factual violations are replaced with a graph fact that itself verifies and is
        not already stated elsewhere. A true claim that is only cognitively
        inappropriate is replaced with prerequisite-review guidance instead of being
        silently swapped for different content. A replacement that would duplicate
        another sentence removes the violating sentence.
        """
        scaffold = self.scaffold(c3_path)
        others = {item for position, item in enumerate(sentences) if position != index}
        replacement, strategy = scaffold, "prerequisite-review guidance"
        if verified.factual_status != "ENTAILED" and self.config.check_factual:
            concepts = self.kg.get("concepts", {})
            ordered = [c3_path["target"]]
            ordered += [c for c in verified.claim.concept_ids if c not in ordered]
            for concept_id in ordered:
                for fact in concepts.get(concept_id, {}).get("facts", []):
                    if fact in others:
                        continue
                    candidate = self._verify_claim(
                        self._build_claim(index + 1, fact), c3_path, learner_state
                    )
                    if candidate.accepted:
                        return fact, "graph-fact replacement"
        if replacement in others:
            return "", "removed (replacement already stated)"
        return replacement, strategy

    def scaffold(self, c3_path: dict[str, Any]) -> str:
        target = self.kg.get("concepts", {}).get(c3_path["target"], {})
        name = target.get("name", c3_path["target"].replace("_", " ").title())
        return (
            f"For {name}, review the earlier concepts on your verified learning path "
            "that are not yet secure before continuing."
        )

    def _is_guidance(self, text: str, c3_path: dict[str, Any]) -> bool:
        return text == self.scaffold(c3_path)

    def _review_first(
        self,
        initial_claims: list[VerifiedClaim],
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
    ) -> list[str]:
        needed: list[str] = []
        for verified in initial_claims:
            if not any(v in verified.violations for v in
                       ("UNMASTERED_PREREQUISITE", "INCONCLUSIVE_COGNITIVE")):
                continue
            for concept_id in verified.claim.concept_ids:
                if concept_id != c3_path["target"] and concept_id not in needed and \
                        self._mastery_state(concept_id, learner_state) != "MASTERED":
                    needed.append(concept_id)
        return needed

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def _stem(word: str) -> str:
        return word[:-1] if word.endswith("s") and len(word) > 3 else word

    @classmethod
    def _content_words(cls, text: str) -> set[str]:
        words = (cls._stem(word) for word in re.findall(r"[a-z0-9]+", text.lower()))
        return {word for word in words if word not in STOPWORDS and word not in NEGATIONS}

    @staticmethod
    def _estimate_bloom(sentence: str) -> int:
        words = set(re.findall(r"[a-z]+", sentence.lower()))
        for level, cues in BLOOM_CUES:
            if words & set(cues):
                return level
        return 1

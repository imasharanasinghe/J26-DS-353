from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from . import grounding
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
MISCONCEPTION_PREFIX = "contradicts graph misconception: "
HEADING = re.compile(r"^(#{1,4})\s+(.*)$")
BULLET = re.compile(r"^([-*\u2022]|\d+[.)])\s+(.*)$")

# Verb cues for the pilot Bloom estimator (revised taxonomy level per cue).
BLOOM_CUES: tuple[tuple[int, tuple[str, ...]], ...] = (
    (6, ("design", "create", "construct", "develop")),
    (5, ("evaluate", "justify", "critique", "assess")),
    (4, ("analyze", "analyse", "compare", "differentiate", "examine")),
    (3, ("implement", "apply", "solve", "compute")),
    (2, ("explain", "describe", "why", "summarize")),
)


@dataclass
class _Line:
    """One line of the explanation. Headings and the path diagram carry no claims."""

    kind: str  # heading | path | blank | bullet | text
    raw: str = ""
    prefix: str = ""
    level: int = 0
    claims: list[str] = field(default_factory=list)


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
    final_layout: list[dict[str, Any]] = field(default_factory=list)

    @property
    def metrics(self) -> dict[str, Any]:
        return summarize(self)

    def to_dict(self) -> dict:
        return {
            "schema_version": "c4-report/1.1",
            "learner_id": self.learner_id,
            "target": self.target,
            "verified_path": self.verified_path,
            "original_explanation": self.original_explanation,
            "final_explanation": self.final_explanation,
            "final_layout": self.final_layout,
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
        lines = self._parse(explanation, grounding.path_line(c3_path, self.kg))
        sentences = self._flat(lines)
        initial_claims = self._verify_all(sentences, c3_path, learner_state)
        claims = initial_claims
        trace: list[RewriteStep] = []
        attempts = 0
        while (
            self.config.rewrite
            and any(not claim.accepted for claim in claims)
            and attempts < self.config.max_rewrite_attempts
        ):
            replacements: dict[tuple[int, int], list[str]] = {}
            produced: set[str] = set()
            position = 0
            for line_no, line in enumerate(lines):
                for slot, text in enumerate(line.claims):
                    verified = claims[position]
                    position += 1
                    if verified.accepted:
                        continue
                    others = {item for item in self._flat(lines) if item != text} | produced
                    replacement, strategy = self._rewrite(verified, others, c3_path, learner_state)
                    if replacement == [text]:
                        continue
                    replacements[(line_no, slot)] = replacement
                    produced.update(replacement)
                    trace.append(RewriteStep(
                        attempts + 1, verified.claim.claim_id, tuple(verified.violations),
                        text, " ".join(replacement), strategy,
                    ))
                    verified.rewritten_text = " ".join(replacement)
            if not replacements:
                break
            lines = self._apply(lines, replacements)
            sentences = self._flat(lines)
            attempts += 1
            claims = self._verify_all(sentences, c3_path, learner_state)

        lines = self._tidy(lines)
        unresolved = [claim.claim.claim_id for claim in claims if not claim.accepted]
        return C4Result(
            learner_id=c3_path["learner_id"],
            target=c3_path["target"],
            verified_path=True,
            original_explanation=explanation,
            final_explanation=self._render(lines),
            initial_claims=initial_claims,
            claims=claims,
            rewrite_attempts=attempts,
            unresolved_claims=unresolved,
            trace=trace,
            review_first=self._review_first(initial_claims, c3_path, learner_state),
            latency_s=time.perf_counter() - started,
            config=asdict(self.config),
            final_layout=self._layout(lines),
        )

    # ------------------------------------------------------- structure and layout

    def _parse(self, explanation: str, path_line: str) -> list[_Line]:
        """Split an explanation into lines; every sentence on a text or bullet line is a claim.

        Headings are structure, not claims. The path diagram is static only when it is
        exactly the line C4 would write for this verified path; anything else is a claim.
        """
        lines: list[_Line] = []
        for raw in explanation.strip().splitlines():
            stripped = raw.strip()
            if not stripped:
                lines.append(_Line("blank"))
                continue
            heading = HEADING.match(stripped)
            if heading:
                lines.append(_Line("heading", raw=stripped, level=len(heading.group(1))))
                continue
            if stripped == path_line:
                lines.append(_Line("path", raw=stripped))
                continue
            bullet = BULLET.match(stripped)
            kind, prefix, body = "text", "", stripped
            if bullet:
                marker = bullet.group(1)
                kind, prefix, body = "bullet", ("-" if marker in ("*", "\u2022") else marker) + " ", bullet.group(2)
            claims = self._split(body)
            if claims:
                lines.append(_Line(kind, prefix=prefix, claims=claims))
        return lines

    @staticmethod
    def _flat(lines: list[_Line]) -> list[str]:
        return [claim for line in lines for claim in line.claims]

    @staticmethod
    def _apply(lines: list[_Line], replacements: dict[tuple[int, int], list[str]]) -> list[_Line]:
        """Splice replacement sentences in; a repaired bullet becomes one bullet per sentence."""
        result: list[_Line] = []
        for line_no, line in enumerate(lines):
            if not line.claims:
                result.append(line)
                continue
            updated: list[str] = []
            for slot, text in enumerate(line.claims):
                updated.extend(replacements.get((line_no, slot), [text]))
            touched = any((line_no, slot) in replacements for slot in range(len(line.claims)))
            if line.kind == "bullet" and touched:
                result.extend(_Line("bullet", prefix=line.prefix, claims=[item]) for item in updated)
            else:
                result.append(replace(line, claims=updated))
        return result

    @staticmethod
    def _tidy(lines: list[_Line]) -> list[_Line]:
        """Drop emptied lines, headings with no content left, and repeated blank lines."""
        live = [line for line in lines if line.kind in ("heading", "path", "blank") or line.claims]
        kept: list[_Line] = []
        for index, line in enumerate(live):
            if line.kind == "heading":
                has_content = False
                for following in live[index + 1:]:
                    if following.kind == "heading" and following.level <= line.level:
                        break
                    if following.kind in ("bullet", "text", "path"):
                        has_content = True
                        break
                if not has_content:
                    continue
            if line.kind == "blank" and (not kept or kept[-1].kind == "blank"):
                continue
            kept.append(line)
        while kept and kept[-1].kind == "blank":
            kept.pop()
        return kept

    @staticmethod
    def _render(lines: list[_Line]) -> str:
        out: list[str] = []
        for line in lines:
            if line.kind in ("heading", "path"):
                out.append(line.raw)
            elif line.kind == "blank":
                out.append("")
            else:
                out.append(line.prefix + " ".join(line.claims))
        return "\n".join(out)

    @staticmethod
    def _layout(lines: list[_Line]) -> list[dict[str, Any]]:
        """Lines with the ids of the final claims they hold, for rendering the report."""
        layout: list[dict[str, Any]] = []
        number = 0
        for line in lines:
            if line.kind in ("heading", "path"):
                text = line.raw.lstrip("#").strip() if line.kind == "heading" else line.raw
                layout.append({"kind": line.kind, "level": line.level, "text": text, "claim_ids": []})
            elif line.kind == "blank":
                continue
            else:
                ids = [f"claim-{number + offset}" for offset in range(1, len(line.claims) + 1)]
                number += len(line.claims)
                layout.append({"kind": line.kind, "level": 0, "text": "", "claim_ids": ids})
        return layout

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
        grounded = self.grounded_texts(c3_path, learner_state).get(claim.text)
        if grounded:
            claim = replace(claim, source="grounded")
        factual_status, evidence = self._check_factual(claim, grounded)
        cognitive_status = self._check_cognitive(claim, c3_path, learner_state, grounded)
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
        if grounded:
            confidence = "MEDIUM" if not violations else "LOW"
        elif factual_status == "ENTAILED" and cognitive_status == "APPROPRIATE":
            confidence = "HIGH"
        elif evidence:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"
        return VerifiedClaim(claim, factual_status, cognitive_status, evidence, violations, confidence)

    def _check_factual(
        self, claim: Claim, grounded: str | None = None
    ) -> tuple[FactualStatus, list[str]]:
        """Rule-based graph-edge mapping: compare content words with graph statements."""
        if grounded:
            return "ENTAILED", [f"written by C4 from the {grounded}; asserts no unverified domain fact"]
        concepts = self.kg.get("concepts", {})
        facts: list[str] = []
        known_false: list[str] = []
        for concept_id in claim.concept_ids:
            facts.extend(self._graph_statements(concept_id))
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
                return "CONTRADICTED", [f"{MISCONCEPTION_PREFIX}{statement}"]

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

    def _mastery_detail(
        self, concept_id: str, learner_state: dict[str, Any]
    ) -> tuple[str, str | None]:
        """State plus, for UNKNOWN, why: no_history, borderline, or uncertain."""
        mastery = learner_state.get("mastery", {})
        uncertainty = learner_state.get("uncertainty", {})
        if concept_id not in mastery:
            return "UNKNOWN", "no_history"
        score = float(mastery[concept_id])
        threshold = self.config.mastery_threshold
        if abs(score - threshold) < self.config.threshold_margin:
            return "UNKNOWN", "borderline"
        if score < threshold:
            return "UNMASTERED", None
        if float(uncertainty.get(concept_id, 1.0)) > self.config.uncertainty_threshold:
            return "UNKNOWN", "uncertain"
        return "MASTERED", None

    def _mastery_state(self, concept_id: str, learner_state: dict[str, Any]) -> str:
        return self._mastery_detail(concept_id, learner_state)[0]

    def _check_cognitive(
        self, claim: Claim, c3_path: dict[str, Any], learner_state: dict[str, Any],
        grounded: str | None = None,
    ) -> CognitiveStatus:
        """Bloom ceiling first, then mastery of every non-target concept the claim relies on.

        The current target is exempt: being new to the learner is not a violation.
        """
        if grounded:
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
        others: set[str],
        c3_path: dict[str, Any],
        learner_state: dict[str, Any],
    ) -> tuple[list[str], str]:
        """Targeted replacement for one violating sentence; returns replacement sentences.

        - Factual violation: the closest graph fact that itself verifies for this learner.
        - Unmastered or uncertain prerequisite: one sentence per concept, built from the
          learner's own mastery and the verified path, saying what to review or check.
        - Bloom mismatch: a sentence saying the question is saved for later, then a
          graph fact at the learner's level.
        A replacement already stated elsewhere is dropped so nothing is said twice.
        """
        claim, target = verified.claim, c3_path["target"]
        violations = set(verified.violations)
        if self.config.check_factual and verified.factual_status != "ENTAILED":
            myth = next((item[len(MISCONCEPTION_PREFIX):] for item in verified.evidence
                         if item.startswith(MISCONCEPTION_PREFIX)), None)
            correction = [grounding.misconception_sentence(myth)] if myth else []
            fact = self._best_fact(claim, others | set(correction), c3_path, learner_state)
            if correction or fact:
                chosen = [item for item in correction + ([fact] if fact else []) if item not in others]
                label = "misconception correction" + (" + graph fact" if fact else "")
                return chosen, label if correction else "graph-fact replacement"
        replacement: list[str] = []
        strategy = "removed (no verified replacement available)"
        if self.config.check_cognitive:
            if violations & {"UNMASTERED_PREREQUISITE", "INCONCLUSIVE_COGNITIVE"}:
                insecure = [
                    concept_id for concept_id in claim.concept_ids
                    if concept_id != target and self._mastery_state(concept_id, learner_state) != "MASTERED"
                ]
                replacement += [self.status_sentence(item, c3_path, learner_state) for item in insecure]
                unmastered = any(self._mastery_state(item, learner_state) == "UNMASTERED" for item in insecure)
                strategy = "prerequisite-review guidance" if unmastered else "prerequisite-check guidance"
            if "BLOOM_MISMATCH" in violations:
                ceiling = self._bloom_ceiling(c3_path, learner_state)
                replacement.append(grounding.bloom_sentence(claim.estimated_bloom_level or 1, ceiling))
                fact = self._best_fact(claim, others | set(replacement), c3_path, learner_state)
                if fact:
                    replacement.append(fact)
                strategy = "bloom deferral + graph fact"
        replacement = [item for item in dict.fromkeys(replacement) if item not in others]
        if not replacement:
            return [], "removed (already stated elsewhere)" if strategy != "removed (no verified replacement available)" else strategy
        return replacement, strategy

    def _best_fact(
        self, claim: Claim, others: set[str], c3_path: dict[str, Any], learner_state: dict[str, Any]
    ) -> str | None:
        """First graph fact, preferring the claim's own concepts, that verifies for this learner."""
        concepts = self.kg.get("concepts", {})
        ordered = [item for item in claim.concept_ids if item in concepts]
        if c3_path["target"] not in ordered:
            ordered.append(c3_path["target"])
        for concept_id in ordered:
            for fact in concepts.get(concept_id, {}).get("facts", []):
                if fact in others:
                    continue
                candidate = self._verify_claim(self._build_claim(0, fact), c3_path, learner_state)
                if candidate.accepted:
                    return fact
        return None

    # --------------------------------------------- sentences written from learner data

    def concept_name(self, concept_id: str) -> str:
        return grounding.concept_name(self.kg, concept_id)

    def path_concepts(self, c3_path: dict[str, Any]) -> list[str]:
        """Concepts the learner meets before the target, in path order."""
        seen: list[str] = []
        for step in c3_path.get("path", []):
            concept_id = step.get("id")
            if step.get("kind") in ("learn", "probe") and concept_id and \
                    concept_id != c3_path["target"] and concept_id not in seen:
                seen.append(concept_id)
        return seen

    def _relation(self, concept_id: str, c3_path: dict[str, Any]) -> str | None:
        target = self.kg.get("concepts", {}).get(c3_path["target"], {})
        if concept_id in target.get("prerequisites", []):
            return "prerequisite"
        if concept_id in self.path_concepts(c3_path):
            return "earlier"
        return None

    def status_sentence(self, concept_id: str, c3_path: dict[str, Any], learner_state: dict[str, Any]) -> str:
        """What the learner should do about one concept, from C2 mastery and the C3 path."""
        state, reason = self._mastery_detail(concept_id, learner_state)
        name = self.concept_name(concept_id)
        mastery = learner_state.get("mastery", {}).get(concept_id)
        uncertainty = learner_state.get("uncertainty", {}).get(concept_id)
        mastery = None if mastery is None else float(mastery)
        uncertainty = None if uncertainty is None else float(uncertainty)
        if state == "MASTERED":
            return grounding.known_sentence(name, mastery)
        if state == "UNMASTERED":
            return grounding.review_sentence(
                name, mastery, self.config.mastery_threshold,
                self.concept_name(c3_path["target"]), self._relation(concept_id, c3_path))
        threshold = self.config.uncertainty_threshold if reason == "uncertain" else self.config.mastery_threshold
        return grounding.check_sentence(name, reason or "no_history", mastery, uncertainty, threshold)

    def next_concept(self, c3_path: dict[str, Any], learner_state: dict[str, Any]) -> str:
        """First concept on the path the learner has not secured, else the target."""
        for concept_id in self.path_concepts(c3_path):
            if self._mastery_state(concept_id, learner_state) != "MASTERED":
                return concept_id
        return c3_path["target"]

    def next_sentence(self, c3_path: dict[str, Any], learner_state: dict[str, Any]) -> str:
        return grounding.next_sentence(self.concept_name(self.next_concept(c3_path, learner_state)))

    def misconception_sentences(self, concept_id: str) -> list[str]:
        concept = self.kg.get("concepts", {}).get(concept_id, {})
        return [grounding.misconception_sentence(item) for item in concept.get("known_false", [])]

    def prerequisite_sentences(self, concept_id: str) -> list[str]:
        """Graph-derived statements 'Before X, you need Y.'; checked against C1, not grounded."""
        concepts = self.kg.get("concepts", {})
        name = self.concept_name(concept_id)
        return [
            grounding.prerequisite_sentence(name, self.concept_name(item))
            for item in concepts.get(concept_id, {}).get("prerequisites", []) if item in concepts
        ]

    def _graph_statements(self, concept_id: str) -> list[str]:
        facts = list(self.kg.get("concepts", {}).get(concept_id, {}).get("facts", []))
        return facts + self.prerequisite_sentences(concept_id)

    def grounded_texts(self, c3_path: dict[str, Any], learner_state: dict[str, Any]) -> dict[str, str]:
        """Every sentence C4 itself would write for this path and learner, with its data source.

        The verifier treats an exact match as grounded. Nothing else is: a model sentence
        that only resembles one of these goes through the normal checks.
        """
        cached = getattr(self, "_ground_cache", None)
        if cached and cached[0] is c3_path and cached[1] is learner_state:
            return cached[2]
        texts = {grounding.path_line(c3_path, self.kg): grounding.SOURCE_PATH}
        concepts = self.kg.get("concepts", {})
        for concept_id, concept in concepts.items():
            if concept_id != c3_path["target"]:
                texts[self.status_sentence(concept_id, c3_path, learner_state)] = grounding.SOURCE_LEARNER
            for item in self.misconception_sentences(concept_id):
                texts[item] = grounding.SOURCE_GRAPH
        ceiling = self._bloom_ceiling(c3_path, learner_state)
        for level in range(ceiling + 1, 7):
            texts[grounding.bloom_sentence(level, ceiling)] = grounding.SOURCE_LEARNER
        texts[self.next_sentence(c3_path, learner_state)] = grounding.SOURCE_PATH
        self._ground_cache = (c3_path, learner_state, texts)
        return texts

    def visual(self, c3_path: dict[str, Any], learner_state: dict[str, Any]) -> dict[str, Any]:
        """Per-step state for the path diagram: what the learner has secured and what is next."""
        target = c3_path["target"]
        nodes: list[dict[str, Any]] = []
        for step in c3_path.get("path", []):
            if step.get("kind") == "remediate":
                nodes.append({"id": step.get("id"), "kind": "remediate", "state": "FIX",
                              "name": f"Fix: {self.concept_name(step.get('affects', ''))} misconception"})
                continue
            concept_id = step["id"]
            state = "TARGET" if concept_id == target else self._mastery_state(concept_id, learner_state)
            mastery = learner_state.get("mastery", {}).get(concept_id)
            uncertainty = learner_state.get("uncertainty", {}).get(concept_id)
            nodes.append({
                "id": concept_id, "kind": step.get("kind"), "state": state,
                "name": step.get("name") or self.concept_name(concept_id),
                "mastery": None if mastery is None else float(mastery),
                "uncertainty": None if uncertainty is None else float(uncertainty),
            })
        ceiling = self._bloom_ceiling(c3_path, learner_state)
        return {
            "nodes": nodes,
            "next": self.next_concept(c3_path, learner_state),
            "bloom_ceiling": ceiling,
            "bloom_ceiling_name": grounding.BLOOM_NAMES.get(ceiling, str(ceiling)),
            "mastery_threshold": self.config.mastery_threshold,
            "uncertainty_threshold": self.config.uncertainty_threshold,
        }

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

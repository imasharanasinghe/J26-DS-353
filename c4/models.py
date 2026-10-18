from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

FactualStatus = Literal["ENTAILED", "CONTRADICTED", "UNSUPPORTED"]
CognitiveStatus = Literal[
    "APPROPRIATE", "BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE", "INCONCLUSIVE"
]

FACTUAL_VIOLATIONS = ("CONTRADICTED_CLAIM", "UNSUPPORTED_CLAIM")
COGNITIVE_VIOLATIONS = ("BLOOM_MISMATCH", "UNMASTERED_PREREQUISITE")


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    concept_ids: tuple[str, ...] = ()
    estimated_bloom_level: int | None = None


@dataclass
class VerifiedClaim:
    claim: Claim
    factual_status: FactualStatus
    cognitive_status: CognitiveStatus
    evidence: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
    rewritten_text: str | None = None

    @property
    def accepted(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim.claim_id,
            "text": self.claim.text,
            "concept_ids": list(self.claim.concept_ids),
            "estimated_bloom_level": self.claim.estimated_bloom_level,
            "factual_status": self.factual_status,
            "cognitive_status": self.cognitive_status,
            "evidence": self.evidence,
            "violations": self.violations,
            "confidence": self.confidence,
            "accepted": self.accepted,
            "rewritten_text": self.rewritten_text,
        }


@dataclass(frozen=True)
class RewriteStep:
    """One targeted replacement, recorded for the rewrite/re-verification trace."""

    attempt: int
    claim_id: str
    violations: tuple[str, ...]
    before: str
    after: str
    strategy: str

    def to_dict(self) -> dict:
        return {
            "attempt": self.attempt,
            "claim_id": self.claim_id,
            "violations": list(self.violations),
            "before": self.before,
            "after": self.after,
            "strategy": self.strategy,
        }

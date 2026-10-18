"""All tunable numbers in one place. Change them here, not inside the code."""
from dataclasses import dataclass


@dataclass
class C3Config:
    # A concept counts as "known" when mastery >= this.
    mastery_threshold: float = 0.7
    # The student model is "unsure" about a concept when uncertainty >= this -> probe it.
    uncertainty_threshold: float = 0.25
    # ZPD rule: a new concept may be at most this many difficulty levels above
    # the hardest thing the learner knows so far.
    zpd_width: int = 1
    # Bloom rule: the thinking level (Remember=1 ... Create=6) may rise by at most
    # this much above the highest level reached so far. Only used when the
    # knowledge graph has Bloom levels (C1's HAS_BLOOM_LEVEL edge).
    check_bloom: bool = True
    bloom_width: int = 1
    # L3: how many draft paths the proposer writes.
    k_drafts: int = 3
    # L5: maximum repair rounds per draft (VETTING and LLM-Modulo also cap the loop).
    max_repair_rounds: int = 3
    # Which critic rules are switched on (handy for per-rule ablation).
    rules: tuple = ("R1", "R2", "R3", "R4", "R5")

from __future__ import annotations

import pytest

from c4.progression import (
    ConceptProgress,
    LearnerProgress,
    ProgressionConfig,
    decide,
    scaffold_for,
    update,
)

CFG = ProgressionConfig()


def test_new_concept_starts_at_remember_with_full_support() -> None:
    decision = decide(ConceptProgress(), ready=True)
    assert (decision.target_level, decision.action, decision.scaffold) == (1, "start", "full")


def test_ready_learner_is_aimed_one_level_above_the_demonstrated_level() -> None:
    decision = decide(ConceptProgress(level=2), ready=True)
    assert (decision.target_level, decision.action, decision.current_level) == (3, "advance", 2)


def test_learner_with_unsecured_prerequisites_consolidates_instead_of_advancing() -> None:
    decision = decide(ConceptProgress(level=2), ready=False)
    assert (decision.target_level, decision.action) == (2, "consolidate")


def test_consolidation_never_drops_below_remember() -> None:
    # a seeded level of 0 with history still targets level 1, not 0
    progress = update(ConceptProgress(), 1, 1, 0.2)
    assert decide(progress, ready=False).target_level == 1


def test_top_level_is_maintained_not_exceeded() -> None:
    decision = decide(ConceptProgress(level=6), ready=True)
    assert (decision.target_level, decision.action) == (6, "maintain")


def test_passing_a_stretch_task_raises_the_demonstrated_level() -> None:
    progress = update(ConceptProgress(level=2), 1, 3, 0.9)
    assert progress.level == 3
    assert decide(progress, ready=True).target_level == 4


def test_failing_a_stretch_task_does_not_lower_the_level_and_triggers_a_retry() -> None:
    progress = ConceptProgress(level=2)
    for session in (1, 2, 3):
        progress = update(progress, session, 3, 0.1)
    assert progress.level == 2
    decision = decide(progress, ready=True)
    assert (decision.target_level, decision.action, decision.scaffold) == (3, "retry", "full")


def test_failing_a_demonstrated_level_twice_demotes_once() -> None:
    progress = update(ConceptProgress(level=2), 1, 2, 0.1)
    assert progress.level == 2  # one failure is not enough
    progress = update(progress, 2, 2, 0.2)
    assert progress.level == 1


def test_a_pass_between_failures_resets_the_demotion_streak() -> None:
    progress = ConceptProgress(level=2)
    for session, score in enumerate((0.1, 0.9, 0.1), 1):
        progress = update(progress, session, 2, score)
    assert progress.level == 2


def test_middling_score_neither_promotes_nor_demotes() -> None:
    progress = update(ConceptProgress(level=2), 1, 3, 0.55)
    assert progress.level == 2


def test_support_fades_with_consecutive_passes_and_returns_after_a_failure() -> None:
    progress = ConceptProgress()
    assert scaffold_for(progress, CFG) == "full"
    progress = update(progress, 1, 1, 0.9)
    assert scaffold_for(progress, CFG) == "partial"
    progress = update(progress, 2, 2, 0.9)
    assert scaffold_for(progress, CFG) == "minimal"
    progress = update(progress, 3, 3, 0.3)
    assert scaffold_for(progress, CFG) == "full"


def test_update_does_not_mutate_its_input() -> None:
    original = ConceptProgress(level=1)
    update(original, 1, 2, 0.9)
    assert original.level == 1 and original.attempts == []


@pytest.mark.parametrize("level,score", [(0, 0.5), (7, 0.5), (2, -0.1), (2, 1.1)])
def test_update_rejects_out_of_range_input(level: int, score: float) -> None:
    with pytest.raises(ValueError):
        update(ConceptProgress(), 1, level, score)


def test_learner_progress_round_trips_through_learner_state() -> None:
    progress = LearnerProgress().with_attempt("heap", 1, 1, 0.9).with_attempt("heap", 2, 2, 0.8)
    restored = LearnerProgress.from_state({"bloom": progress.to_state()})
    assert restored.get("heap").level == 2
    assert [item.level for item in restored.get("heap").attempts] == [1, 2]
    assert restored.get("never_seen").level == 0


@pytest.mark.parametrize("bad", [[], "x", {"heap": {"level": 9}}])
def test_malformed_bloom_state_is_rejected(bad) -> None:
    with pytest.raises((ValueError, AttributeError, TypeError)):
        LearnerProgress.from_state({"bloom": bad})

from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4.bloom import estimate_level, estimate_level_v2, is_task, score_estimator
from c4.evaluation import evaluate_bloom

ITEMS = Path(__file__).resolve().parents[1] / "c4" / "data" / "bloom_items.json"


def test_item_set_is_balanced_and_split_without_overlap() -> None:
    document = json.loads(ITEMS.read_text(encoding="utf-8"))
    items = document["items"]
    assert len({item["id"] for item in items}) == len(items) == 90
    for split, expected in (("dev", 6), ("test", 6), ("hard", 3)):
        for level in range(1, 7):
            assert sum(i["split"] == split and i["level"] == level for i in items) == expected
    assert len({item["text"] for item in items}) == len(items)


@pytest.mark.parametrize("text,expected", [
    ("Why is array indexing fast?", True),
    ("Explain why recursion needs a base case.", True),
    ("Please compare the two traversals.", True),
    ("A heap can be used to build priority queues.", False),
    ("Hint: break Heaps into its smallest steps and take them one at a time.", False),
])
def test_task_detection_separates_instructions_from_statements(text: str, expected: bool) -> None:
    assert is_task(text) is expected


def test_v2_does_not_turn_ordinary_statements_into_demanding_tasks() -> None:
    statement = "Recursion is often used to solve problems and to build tree traversals."
    assert estimate_level(statement) == 3          # V1 over-reads the verb cues
    assert estimate_level_v2(statement) == 1


def test_phrase_cues_and_polite_frames() -> None:
    assert estimate_level_v2("In your own words, what does the base case do?") == 2
    assert estimate_level_v2("Can you design a queue that never overflows?") == 6
    assert estimate_level_v2("Which part of this loop causes the slowdown?") == 4


def test_scoring_counts_a_confusion_matrix_and_within_one() -> None:
    items = [{"text": "a", "level": 1}, {"text": "b", "level": 3}, {"text": "c", "level": 5}]
    answers = {"a": 1, "b": 2, "c": 2}
    result = score_estimator(items, lambda text: answers[text])
    assert result["accuracy"] == 33.3 and result["within_one"] == 66.7
    assert result["confusion"]["5"]["2"] == 1 and result["mean_abs_error"] == round(4 / 3, 3)


def test_evaluation_reports_each_split_and_keeps_the_limits_visible() -> None:
    result = evaluate_bloom(ITEMS)
    assert set(result["splits"]) == {"dev", "test", "hard"}
    assert result["splits"]["test"]["v2"]["accuracy"] > result["splits"]["test"]["v1"]["accuracy"]
    assert result["splits"]["hard"]["v2"]["accuracy"] < 50  # verb cues cannot read indirect phrasing
    assert "single annotator" in result["provenance"] and "no inter-annotator" in result["caveat"]

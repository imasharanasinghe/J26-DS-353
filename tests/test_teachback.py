from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4 import synthetic, teachback
from c4.novice import LexicalNovice

KG = json.loads((Path(__file__).resolve().parents[1] / "c4" / "data" / "knowledge_graph.json").read_text())
NOVICE = LexicalNovice(KG)
HEAPS = ["heap", "binary_tree", "arrays"]


def test_prompt_names_graph_prerequisites() -> None:
    prompt = teachback.make_prompt(KG, "heap")
    assert "Binary Trees" in prompt["text"] and "Arrays" in prompt["text"]
    assert prompt["required_concepts"] == ["binary_tree", "arrays"]


def test_coverage_uses_longest_match() -> None:
    result = teachback.coverage(KG, "A heap is stored in an array. It is a binary tree.", ["heap", "tree", "binary_tree"])
    assert "binary_tree" in result["present"] and "tree" in result["missing"]


def test_claim_check_flags_known_false_statement() -> None:
    result = teachback.claim_check(KG, "A heap is always fully sorted. A heap is a complete binary tree.")
    assert any("always fully sorted" in text for text in result["contradicted"])
    assert result["counts"]["ENTAILED"] >= 1


def test_good_explanation_beats_wrong_and_empty() -> None:
    good = teachback.score_exam(KG, NOVICE, "S1", synthetic.explain(KG, "complete", 0, HEAPS), HEAPS)
    wrong = teachback.score_exam(KG, NOVICE, "S2", synthetic.explain(KG, "wrong", 0, HEAPS), HEAPS)
    empty = teachback.score_exam(KG, NOVICE, "S3", "", HEAPS)
    score = lambda r: r["novice_test"]["overall"]["score"]
    assert score(good) > score(wrong) >= score(empty) == 0.0
    assert wrong["flags"] and empty["flags"]


def test_evidence_message_format() -> None:
    result = teachback.score_exam(KG, NOVICE, "S1", synthetic.explain(KG, "complete", 0, HEAPS), HEAPS, "2026-w07-v3")
    message = result["evidence"][0]
    assert {"student", "concept", "bloom", "score", "items", "source", "weight", "graph_version", "thin"} <= set(message)
    assert message["source"] == "teachback_exam" and message["graph_version"] == "2026-w07-v3"
    assert {m["concept"] for m in result["evidence"]} <= set(HEAPS)


def test_no_items_is_an_error() -> None:
    with pytest.raises(ValueError):
        teachback.score_exam(KG, NOVICE, "S1", "x", ["nonexistent"])


def test_cohort_report_lists_concept_means() -> None:
    report = teachback.cohort_report(KG, NOVICE, {"a": synthetic.explain(KG, "complete", 0, HEAPS), "b": ""}, HEAPS)
    assert set(report["students"]) == {"a", "b"} and report["concept_means"]["heap"] == 0.5

from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4.novice import LexicalNovice, OllamaNovice, TextEvidence, graph_universe, parse_answer, summarise, take_test
from c4.testbank import build_test, concept_levels

KG = json.loads((Path(__file__).resolve().parents[1] / "c4" / "data" / "knowledge_graph.json").read_text())
FACTS = " ".join(f for c in KG["concepts"].values() for f in c["facts"])


def test_bank_answers_come_from_graph_and_cover_all_levels() -> None:
    items = build_test(KG)
    assert len(items) >= 20
    universe = graph_universe(KG)
    for item in items:
        for statement in item["requires"]:
            assert statement.removeprefix("NOT: ") in universe, item["id"]
    levels = {level for value in concept_levels(items).values() for level in value}
    assert {1, 2, 3, 4} <= levels


def test_empty_text_gives_zero_knowledge() -> None:
    results = take_test(LexicalNovice(KG), "", build_test(KG))
    assert summarise(results)["all"]["score"] == 0.0
    assert all(row["abstained"] for row in results)


def test_full_text_scores_high_and_false_belief_is_not_credited() -> None:
    novice, items = LexicalNovice(KG), build_test(KG)
    full = summarise(take_test(novice, FACTS, items))["all"]["score"]
    wrong = summarise(take_test(novice, FACTS.replace("last-in-first-out", "first-in-first-out"), items))["all"]
    assert full > 0.9 and wrong["score"] < full


def test_fifo_text_does_not_state_the_lifo_fact() -> None:
    evidence = TextEvidence("A stack follows the first-in-first-out rule.", graph_universe(KG))
    assert not evidence.states("A stack follows the last-in-first-out rule.")
    assert evidence.states("A stack follows the first-in-first-out rule.")


def test_denial_needs_explicit_negation() -> None:
    universe = graph_universe(KG)
    assert TextEvidence("A heap is not always fully sorted.", universe).states("NOT: A heap is always fully sorted.")
    assert not TextEvidence("A heap is always fully sorted.", universe).states("NOT: A heap is always fully sorted.")


def test_parse_answer_and_ollama_transport_stub() -> None:
    assert parse_answer('{"answer": "B"}', 4) == 1
    assert parse_answer('{"answer": "UNKNOWN"}', 4) is None
    assert parse_answer('{"answer": "F"}', 4) is None
    seen = {}

    def transport(payload):
        seen["prompt"] = payload["messages"][1]["content"]
        return {"message": {"content": '{"answer": "A"}'}}

    novice = OllamaNovice(transport=transport)
    item = build_test(KG)[0]
    assert novice.answer("A heap is a complete binary tree.", item) == 0
    assert "TEXT:" in seen["prompt"] and item["stem"] in seen["prompt"]

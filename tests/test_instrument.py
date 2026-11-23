from __future__ import annotations

import json
from pathlib import Path

from c4 import instrument, synthetic
from c4.novice import LexicalNovice, take_test
from c4.testbank import build_test

KG = json.loads((Path(__file__).resolve().parents[1] / "c4" / "data" / "knowledge_graph.json").read_text())
ITEMS = build_test(KG)
NOVICE = LexicalNovice(KG)


def test_variants_are_built_and_empty_is_empty() -> None:
    for name in synthetic.VARIANTS:
        text = synthetic.explain(KG, name, 0)
        assert (text == "") == (name == "empty")
    assert "always" in synthetic.explain(KG, "complete").lower()  # 'never' kf is denied affirmatively


def test_double_negation_is_not_used_for_denials() -> None:
    assert "never" not in synthetic._denial("Recursion never needs a base case.")


def test_lexical_novice_has_no_leakage_and_no_variance() -> None:
    gate = instrument.run_gate(NOVICE, KG, ITEMS, seeds=3, runs=3)
    assert not gate["leakage"]["leaks"]
    assert gate["reliability"]["sd"] == 0.0 and gate["reliability"]["item_agreement"] == 1.0


def test_content_ordering_holds_but_word_order_blindness_is_reported() -> None:
    result = instrument.discrimination(NOVICE, KG, ITEMS, seeds=3)
    checks = {c["expect"]: c["passes"] for c in result["ordering_checks"]}
    assert checks["complete > missing_one (score)"] and checks["half > empty (score)"]
    assert checks["complete > wrong (net)"]
    # A bag-of-words reader cannot see garbling or paraphrase: the gate must say so, not hide it.
    assert not checks["complete > garbled (score)"]
    assert not result["all_pass"]


def test_weaker_writer_gap_is_measured() -> None:
    result = instrument.fairness(NOVICE, KG, ITEMS, levels=(0.6,), seeds=3)
    assert result["gap_vs_clean_prose"]["weaker_writer_0.6"]["mean_gap"] > 0


def test_depth_adjustment_discounts_untraced_correct_answers() -> None:
    text = synthetic.explain(KG, "complete", 0)
    results = take_test(NOVICE, text, ITEMS)
    full = instrument.depth(text, KG, results, ITEMS)
    assert full["untraced"] == 0 and full["depth_adjusted_score"] == full["raw_score"]
    # Pretend the novice answered an item whose required fact the text never states.
    forged = [dict(row, correct=True, abstained=False) for row in take_test(NOVICE, "", ITEMS)]
    assert instrument.depth("", KG, forged, ITEMS)["depth_adjusted_score"] == 0.0

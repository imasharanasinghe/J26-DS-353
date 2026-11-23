from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4 import layers
from c4.layers import FrozenError, GraphError, GraphStore

KG = json.loads((Path(__file__).resolve().parents[1] / "c4" / "data" / "knowledge_graph.json").read_text())


def test_overlay_inherits_base_and_does_not_mutate_it() -> None:
    overlay = {"remove_edges": [["arrays", "stack"]], "not_covered": ["queue"], "emphasis": {"heap": 2.0}}
    graph = layers.resolve(KG, overlay)
    assert "arrays" not in graph["concepts"]["stack"]["prerequisites"]
    assert graph["concepts"]["queue"]["covered"] is False and graph["concepts"]["heap"]["emphasis"] == 2.0
    assert "arrays" in KG["concepts"]["stack"]["prerequisites"] and "covered" not in KG["concepts"]["queue"]


def test_cycle_is_refused() -> None:
    with pytest.raises(GraphError):
        layers.resolve(KG, {"add_edges": [["heap", "arrays"]]})


def test_nothing_changes_until_a_lecturer_approves() -> None:
    store = GraphStore(KG, "dsa-2026s2")
    proposal = store.propose("remove_edge", {"edge": ["arrays", "stack"]}, "audit", "unsupported")
    store.commit()
    assert "arrays" in store.graph()["concepts"]["stack"]["prerequisites"]
    with pytest.raises(GraphError):
        store.decide(proposal.id, True, "")
    store.decide(proposal.id, True, "Dr. Perera")
    version = store.commit("week 3")
    assert "arrays" not in store.graph()["concepts"]["stack"]["prerequisites"]
    assert version == store.graph()["graph_version"] and store.changelog[-1]["changes"][0]["decided_by"] == "Dr. Perera"


def test_rejected_proposal_is_never_applied() -> None:
    store = GraphStore(KG)
    proposal = store.propose("remove_edge", {"edge": ["arrays", "stack"]}, "audit")
    store.decide(proposal.id, False, "Dr. Perera")
    store.commit()
    assert "arrays" in store.graph()["concepts"]["stack"]["prerequisites"]


def test_frozen_block_blocks_commits_until_unfrozen() -> None:
    store = GraphStore(KG)
    store.decide(store.propose("add_edge", {"edge": ["recursion", "stack"]}, "lecturer").id, True, "L")
    store.freeze("block-1")
    with pytest.raises(FrozenError):
        store.commit()
    before = store.version
    store.unfreeze()
    store.commit()
    assert store.version != before and ["recursion", "stack"] in store.overlay["add_edges"]


def test_commit_that_would_create_a_cycle_keeps_the_old_graph() -> None:
    store = GraphStore(KG)
    store.decide(store.propose("add_edge", {"edge": ["heap", "arrays"]}, "lecturer").id, True, "L")
    version = store.version
    with pytest.raises(GraphError):
        store.commit()
    assert store.version == version and ["heap", "arrays"] not in store.overlay["add_edges"]


def test_audit_report_becomes_proposals_and_contested_lowers_confidence() -> None:
    store = GraphStore(KG)
    report = {"proposals": [{"edge": ["binary_tree", "heap"], "status": "Contested", "evidence": "wide", "proposal": "x",
                             "needs_lecturer": True}]}
    (proposal,) = store.propose_from_audit(report)
    store.decide(proposal.id, True, "L")
    store.commit()
    assert store.graph()["edge_confidence"]["binary_tree->heap"]["status"] == "Contested"


def test_transcript_diff_proposes_not_edits() -> None:
    store = GraphStore(KG)
    made = store.propose_from_transcript_diff({"heap", "stack"}, {"heap", "trie"}, set(KG["concepts"]))
    kinds = {(p.kind, p.payload["concept"]) for p in made}
    assert kinds == {("add_concept", "trie"), ("mark_not_covered", "stack")}
    assert "trie" not in store.graph()["concepts"]


def test_mastery_migration_rules() -> None:
    m, u = {"tree": 0.8, "heap": 0.6}, {"tree": 0.1, "heap": 0.2}
    split = layers.migrate_mastery(m, u, {"kind": "split", "concept": "tree", "into": ["tree_a", "tree_b"]})
    assert split["mastery"]["tree_a"] == 0.8 and split["uncertainty"]["tree_a"] > 0.1 and "tree" not in split["mastery"]
    merge = layers.migrate_mastery(m, u, {"kind": "merge", "concepts": ["tree", "heap"], "into": "both"})
    assert merge["mastery"]["both"] == 0.6 and merge["uncertainty"]["both"] >= 0.2
    edge = layers.migrate_mastery(m, u, {"kind": "add_edge", "edge": ["recursion", "tree"]})
    assert edge["mastery"] == m and edge["recheck"] == ["tree"]
    rename = layers.migrate_mastery(m, u, {"kind": "rename", "concept": "tree", "into": "trees"})
    assert rename["mastery"]["trees"] == 0.8

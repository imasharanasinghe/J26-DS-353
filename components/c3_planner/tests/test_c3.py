"""Run with:  python -m pytest -q"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from c3 import (C3Config, C3Pipeline, Critic, KnowledgeGraph, LearnerState, MockProposer,  # noqa: E402
                Step, build_fallback_path, compute_frontier, load_learners)
from c3.prompts import parse_paths  # noqa: E402
from c3.rl.dataset import build_transitions  # noqa: E402

KG = KnowledgeGraph.from_json(os.path.join(ROOT, "data", "mock_kg.json"))
LEARNERS = load_learners(os.path.join(ROOT, "data", "mock_learners.json"))
CFG = C3Config()
CRITIC = Critic(KG, CFG)


def P(*items):
    return [Step.parse(x) for x in items]


def types(vs):
    return {v.type for v in vs}


BEGINNER = LearnerState("t", {"variables": 0.9, "loops": 0.9, "arrays": 0.9, "functions": 0.9,
                              "recursion": 0.9, "linked_list": 0.9},
                        {"variables": 0.05, "loops": 0.05, "arrays": 0.05, "functions": 0.05,
                         "recursion": 0.05, "linked_list": 0.05})


# ---------------- R1
def test_r1_heap_before_tree_is_caught():
    vs = CRITIC.check(P("heap", "tree", "binary_tree"), BEGINNER, "heap")
    assert any(v.type == "MissingPrerequisite" and v.concept == "heap" for v in vs)


def test_r1_correct_order_passes():
    assert CRITIC.check(P("tree", "binary_tree", "heap"), BEGINNER, "heap") == []


# ---------------- R2
def test_r2_already_known_is_flagged():
    vs = CRITIC.check(P("arrays", "tree", "binary_tree", "heap"), BEGINNER, "heap")
    assert "AlreadyKnown" in types(vs)


def test_r2_cognitive_load_jump():
    lr = LearnerState("t", {"variables": 0.9}, {"variables": 0.05})
    vs = CRITIC.check(P("loops", "arrays", "tree"), lr, "tree")
    assert any(v.type == "CognitiveLoadJump" and v.concept == "tree" for v in vs)


# ---------------- tests on the Neo4j graph copy (4 C1 edge types, with Bloom)
KG4 = KnowledgeGraph.from_json(os.path.join(ROOT, "data", "neo4j_kg_copy.json"))
CRITIC4 = Critic(KG4, CFG)


def test_weak_prerequisite_is_not_enforced():
    # big_o -> heap has weight 0.4, so heap does NOT need big_o
    assert "big_o" not in KG4.prereqs("heap") and "big_o" in KG4.weak_prereqs("heap")


def test_r2_bloom_jump():
    # learner only knows Remember-level 'variables' (Bloom 1); 'functions' is Apply (Bloom 3)
    lr = LearnerState("t", {"variables": 0.9, "loops": 0.9}, {"variables": 0.05, "loops": 0.05})
    lr2 = LearnerState("t", {"variables": 0.9}, {"variables": 0.05})
    vs = CRITIC4.check(P("loops", "functions"), lr2, "functions")
    assert not any(v.type == "BloomJump" for v in vs)  # loops (Understand) bridges 1 -> 3
    vs = CRITIC4.check(P("functions"), LearnerState("t", {"variables": 0.9, "loops": 0.2},
                                                    {"variables": 0.05}), "functions")
    assert any(v.type == "BloomJump" and v.concept == "functions" for v in vs)
    assert lr  # keep linters quiet


def test_r1_late_step_caught():
    # the gap found in the first Neo4j run: recursion (known but unsure) taught AFTER tree
    lr = LEARNERS["L05_uneven"]
    path = P("probe:recursion", "remediate:heap_is_sorted", "linked_list", "tree",
             "binary_tree", "recursion", "heap")
    vs = CRITIC4.check(path, lr, "heap")
    assert any(v.type == "LateStep" and v.concept == "recursion" for v in vs)


def test_neo4j_copy_has_no_dead_ends():
    assert KG4.zpd_warnings(CFG.zpd_width, CFG.bloom_width) == []


@pytest.mark.parametrize("lid", list(LEARNERS))
@pytest.mark.parametrize("target", ["heap", "priority_queue", "bst", "stack", "tree"])
def test_fallback_passes_on_neo4j_copy(lid, target):
    lr = LEARNERS[lid]
    fr = compute_frontier(KG4, lr, target, CFG)
    if fr.target_already_known:
        return
    path = build_fallback_path(KG4, lr, fr, CFG)
    assert CRITIC4.check(path, lr, target) == [], [str(v) for v in CRITIC4.check(path, lr, target)]


# ---------------- R3
def test_r3_structure_faults():
    vs = CRITIC.check(P("tree", "made_up", "tree", "binary_tree", "graph"), BEGINNER, "binary_tree")
    assert {"UnknownStep", "DuplicateStep", "OffPath", "TargetNotLast"} <= types(vs)
    assert "TargetMissing" in types(CRITIC.check(P("tree"), BEGINNER, "heap"))


# ---------------- R4
def test_r4_unsure_prerequisite_needs_probe():
    lr = LEARNERS["L02_intermediate"]  # recursion known but uncertain (0.32)
    vs = CRITIC.check(P("big_o", "hashing", "hash_table", "memoization"), lr, "memoization")
    assert any(v.type == "MissingProbe" and v.concept == "recursion" for v in vs)
    ok = CRITIC.check(P("big_o", "hashing", "hash_table", "probe:recursion",
                        "remediate:recursion_no_base_case", "memoization"), lr, "memoization")
    assert "MissingProbe" not in types(ok)


# ---------------- R5
def test_r5_misconception_must_be_fixed_first():
    lr = LEARNERS["L05_uneven"]  # heap_is_sorted
    fr = compute_frontier(KG, lr, "heap", CFG)
    path = [s for s in build_fallback_path(KG, lr, fr, CFG) if s.kind != "remediate"]
    assert "UnremediatedMisconception" in types(CRITIC.check(path, lr, "heap"))


# ---------------- L7 fallback always valid
@pytest.mark.parametrize("lid", list(LEARNERS))
@pytest.mark.parametrize("target", ["heap", "dijkstra", "avl_tree", "dynamic_programming", "dfs"])
def test_fallback_always_passes_critic(lid, target):
    lr = LEARNERS[lid]
    fr = compute_frontier(KG, lr, target, CFG)
    path = build_fallback_path(KG, lr, fr, CFG)
    if not fr.target_already_known:
        assert CRITIC.check(path, lr, target) == [], [str(v) for v in CRITIC.check(path, lr, target)]


def test_kg_has_no_zpd_dead_ends():
    assert KG.zpd_warnings(CFG.zpd_width) == []


# ---------------- pipeline
def test_pipeline_output_is_always_verified():
    for lid, lr in LEARNERS.items():
        for t in ["heap", "dijkstra", "bst"]:
            res = C3Pipeline(KG, MockProposer(seed=1), CFG).plan(lr, t)
            assert res.verified
            j = res.to_json(KG)
            assert j["verified"] and (j["path"] or res.source == "already_known")


def test_parse_llm_reply_with_fences():
    text = 'Sure!\n```json\n{"paths": [["learn:tree", "probe:recursion", "heap"]]}\n```'
    assert parse_paths(text) == [[Step("learn", "tree"), Step("probe", "recursion"), Step("learn", "heap")]]


def test_rl_dataset_builder():
    rows = [{"student_id": "s1", "concept": "arrays", "timestamp": 1, "score": 2},
            {"student_id": "s1", "concept": "stack", "timestamp": 2, "score": 1}]
    tr = build_transitions(rows)
    assert len(tr) == 2 and tr[1]["state"]["mastery"]["arrays"] == 1.0 and tr[1]["done"]


# ---------------- LLM proposer, with a fake client (no internet needed)
class _FakeClient:
    """Pretends to be Gemini: first reply has a mistake, repair reply fixes it."""
    provider, model, calls, failures = "fake", "fake", 0, 0

    def complete(self, system, user, temperature=0.0, retries=2, tag=""):
        self.calls += 1
        if tag.startswith("propose"):
            return '{"paths": [["binary_tree", "tree", "heap"], ["tree", "binary_tree", "heap"]]}'
        return '{"paths": [["tree", "binary_tree", "heap"]]}'


def test_llm_proposer_flow_with_fake_client():
    from c3 import LLMProposer
    lr = LearnerState("t", {c: 0.9 for c in ["variables", "loops", "arrays", "functions",
                                            "recursion", "linked_list"]},
                      {c: 0.05 for c in ["variables", "loops", "arrays", "functions",
                                         "recursion", "linked_list"]})
    prop = LLMProposer(client=_FakeClient())
    res = C3Pipeline(KG4, prop, C3Config(k_drafts=2)).plan(lr, "heap")
    assert res.verified and [s.ref for s in res.path] == ["tree", "binary_tree", "heap"]
    assert prop.client.calls >= 2 and prop.format_failures == 0

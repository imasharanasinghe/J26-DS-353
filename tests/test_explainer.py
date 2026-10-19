from c4 import OllamaExplanationGenerator


def test_ollama_prompt_contains_personalization_context() -> None:
    prompt = OllamaExplanationGenerator().build_prompt(
        {"target": "heap", "path": [{"id": "binary_tree"}]},
        {"mastery": {"binary_tree": 0.2}},
        {"concepts": {"heap": {
            "prerequisites": ["binary_tree"],
            "facts": ["A heap is a complete binary tree."],
        }}},
    )
    assert "heap" in prompt
    assert "binary_tree" in prompt
    assert "A heap is a complete binary tree." in prompt


def test_ollama_response_cleaner_removes_planning_and_duplicates() -> None:
    text = (
        "We are given the fact. Step 1: reason. "
        "A heap is a complete binary tree. "
        "A heap is a complete binary tree."
    )
    assert OllamaExplanationGenerator._clean_response(text) == (
        "A heap is a complete binary tree."
    )


def test_ollama_prompt_separates_known_from_unmastered_concepts() -> None:
    prompt = OllamaExplanationGenerator().build_prompt(
        {"target": "heap", "path": [{"id": "arrays", "kind": "learn"},
                                    {"id": "binary_tree", "kind": "learn"},
                                    {"id": "heap", "kind": "learn"}]},
        {"mastery": {"arrays": 0.9, "binary_tree": 0.2}},
        {"concepts": {"heap": {"name": "Heaps", "facts": ["A heap is a complete binary tree."]}}},
    )
    assert "already knows: arrays" in prompt
    assert "not mastered yet: binary_tree" in prompt


def test_draft_is_a_structured_personalised_explanation() -> None:
    import json
    from pathlib import Path

    from c4 import C4Pipeline
    from c4.explainer import compose_explanation
    from c4.paths import build_verified_path

    data = Path(__file__).resolve().parents[1] / "c4" / "data"
    kg = json.loads((data / "knowledge_graph.json").read_text(encoding="utf-8"))
    learner = json.loads((data / "learner_state.json").read_text(encoding="utf-8"))
    path = build_verified_path("heap", kg, learner["learner_id"])
    draft = compose_explanation(path, learner, kg, kg["concepts"]["heap"]["facts"])
    assert draft.startswith("## Heaps: your next step") and "\nPath: " in draft
    for heading in ("### About Heaps", "### Before you start", "### Where you stand", "### Common mistakes"):
        assert heading in draft
    assert "Review Binary Trees first: your mastery is 0.00" in draft  # uses the learner's own numbers
    result = C4Pipeline(kg).run(path, learner, draft)
    assert result.unresolved_claims == [] and result.metrics["after"]["cognitive_mismatch_rate"] == 0.0
    assert "A heap is a complete binary tree." not in result.final_explanation  # needs an unmastered concept
    assert "A heap can be stored in an array." in result.final_explanation


def test_composing_without_a_model_body_is_refused() -> None:
    import pytest

    from c4.explainer import compose_explanation

    with pytest.raises(ValueError, match="model's explanation"):
        compose_explanation({"target": "heap", "path": []}, {}, {"concepts": {"heap": {}}}, [])

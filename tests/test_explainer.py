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

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

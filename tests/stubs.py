"""Test double for the language-model draft writer.

The product has no offline draft generator: drafts come from a language model. Tests that need
a draft inject this stub, which "writes" the target concept's graph facts, like a faithful model.
"""

from __future__ import annotations

from typing import Any

from c4 import OllamaExplanationGenerator


class StubGenerator(OllamaExplanationGenerator):
    def __init__(self) -> None:
        super().__init__(model="stub-model")

    def generate_body(self, c3_path: dict[str, Any], learner_state: dict[str, Any],
                      knowledge_graph: dict[str, Any]) -> str:
        return " ".join(knowledge_graph["concepts"][c3_path["target"]]["facts"])

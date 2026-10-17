"""L0 input from C1: the knowledge graph.

Loads the JSON shape documented in docs/interfaces.md. Swap the mock file for
C1's real export (or a Neo4j query) without touching the rest of C3.
"""
from __future__ import annotations

import json
from functools import lru_cache


class KnowledgeGraph:
    def __init__(self, concepts: dict, misconceptions: dict | None = None):
        self.concepts = concepts
        self.misconceptions = misconceptions or {}
        # reverse index: concept -> misconceptions attached to it
        self._mis_by_concept: dict[str, list[str]] = {}
        for mid, m in self.misconceptions.items():
            self._mis_by_concept.setdefault(m["affects"], []).append(mid)
        self._ancestors_cache: dict[str, frozenset] = {}

    # ---------- loading ----------
    @classmethod
    def from_json(cls, path: str) -> "KnowledgeGraph":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        kg = cls(data["concepts"], data.get("misconceptions", {}))
        kg.validate()
        return kg

    # ---------- lookups ----------
    def has(self, c: str) -> bool:
        return c in self.concepts

    def name(self, c: str) -> str:
        return self.concepts.get(c, {}).get("name", c)

    def difficulty(self, c: str) -> int:
        return int(self.concepts[c]["difficulty"])

    def prereqs(self, c: str) -> list[str]:
        return list(self.concepts[c].get("prerequisites", []))

    def ancestors(self, c: str) -> frozenset:
        """Every concept that must come before c (prerequisites of prerequisites, too)."""
        if c in self._ancestors_cache:
            return self._ancestors_cache[c]
        out: set[str] = set()
        stack = list(self.prereqs(c))
        while stack:
            p = stack.pop()
            if p not in out:
                out.add(p)
                stack.extend(self.prereqs(p))
        self._ancestors_cache[c] = frozenset(out)
        return self._ancestors_cache[c]

    # ---------- Bloom level (C1's HAS_BLOOM_LEVEL edge; optional) ----------
    def has_bloom(self) -> bool:
        return any(info.get("bloom_rank") for info in self.concepts.values())

    def bloom_rank(self, c: str) -> int:
        return int(self.concepts[c].get("bloom_rank") or 0)

    def bloom_name(self, c: str) -> str:
        return self.concepts[c].get("bloom") or "-"

    def weak_prereqs(self, c: str) -> list[str]:
        return list(self.concepts[c].get("weak_prerequisites", []))

    def misconceptions_on(self, c: str) -> list[str]:
        return list(self._mis_by_concept.get(c, []))

    def misconception_target(self, m: str) -> str | None:
        return self.misconceptions.get(m, {}).get("affects")

    # ---------- sanity checks ----------
    def validate(self) -> None:
        for c, info in self.concepts.items():
            for p in info.get("prerequisites", []):
                if p not in self.concepts:
                    raise ValueError(f"Concept '{c}' lists unknown prerequisite '{p}'")
        for m, info in self.misconceptions.items():
            if info.get("affects") not in self.concepts:
                raise ValueError(f"Misconception '{m}' points to unknown concept '{info.get('affects')}'")
        # cycle check (a prerequisite loop would make every path impossible)
        state: dict[str, int] = {}

        def visit(c, trail):
            if state.get(c) == 1:
                raise ValueError("Prerequisite cycle: " + " -> ".join(trail + [c]))
            if state.get(c) == 2:
                return
            state[c] = 1
            for p in self.prereqs(c):
                visit(p, trail + [c])
            state[c] = 2

        for c in self.concepts:
            visit(c, [])

    def zpd_warnings(self, zpd_width: int, bloom_width: int | None = None) -> list[str]:
        """Concepts no valid path can reach, because every prerequisite is too easy
        (cognitive load) or too low on Bloom's scale. C1 should add a bridging concept."""
        out = []
        for c in self.concepts:
            ps = self.prereqs(c)
            if ps and max(self.difficulty(p) for p in ps) < self.difficulty(c) - zpd_width:
                out.append(f"{c} (cognitive load)")
            if bloom_width is not None and self.has_bloom() and self.bloom_rank(c):
                before = self.ancestors(c)
                top = max((self.bloom_rank(p) for p in before), default=0)
                if before and top < self.bloom_rank(c) - bloom_width:
                    out.append(f"{c} (Bloom)")
        return out

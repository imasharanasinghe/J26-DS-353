"""Adapters for the incomplete C1, C2, and C3 branch contracts."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_c2_learner(data: dict[str, Any], learner_id: str | None = None) -> dict[str, Any]:
    """Accept C3's single learner shape or C2/C3's ``learners`` collection."""
    if "learners" not in data:
        if "learner_id" not in data:
            raise ValueError("Learner data requires learner_id")
        return data

    learners = {item["learner_id"]: item for item in data["learners"]}
    selected = learner_id or next(iter(learners), None)
    if selected not in learners:
        raise ValueError(f"Learner '{selected}' was not found")
    return learners[selected]


def validate_c3_path(path: dict[str, Any]) -> None:
    required = {"learner_id", "target", "verified", "path"}
    missing = required - path.keys()
    if missing:
        raise ValueError(f"C3 path is missing fields: {sorted(missing)}")
    if not isinstance(path["path"], list):
        raise ValueError("C3 path field must be a list")
    for step in path["path"]:
        if step.get("kind") not in {"learn", "probe", "remediate"}:
            raise ValueError(f"Unsupported C3 step kind: {step.get('kind')}")
        if not step.get("id"):
            raise ValueError("Every C3 path step requires an id")


def load_c1_csv_graph(
    concept_nodes_path: str | Path,
    relations_path: str | Path,
) -> dict[str, Any]:
    """Convert C1's current unverified CSV snapshots to C3-compatible JSON.

    C1's current branch does not export verified facts, so this adapter records
    candidate relations and leaves factual evidence empty until C1 verifies it.
    """
    concepts: dict[str, Any] = {}
    with Path(concept_nodes_path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            name = row["concept"].strip()
            if name:
                concepts[_concept_id(name)] = {
                    "name": name.title(),
                    "difficulty": 1,
                    "prerequisites": [],
                    "candidate_relations": [],
                    "facts": [],
                }

    misconceptions: dict[str, Any] = {}
    with Path(relations_path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            left = _concept_id(row.get("concept_a", ""))
            right = _concept_id(row.get("concept_b", ""))
            relation = row.get("relation_type", "")
            if left not in concepts:
                concepts[left] = {"name": left.replace("_", " ").title(), "difficulty": 1,
                                  "prerequisites": [], "candidate_relations": [], "facts": []}
            if right not in concepts:
                concepts[right] = {"name": right.replace("_", " ").title(), "difficulty": 1,
                                   "prerequisites": [], "candidate_relations": [], "facts": []}
            concepts[right]["candidate_relations"].append(row)
            if relation == "prerequisite-of":
                concepts[right]["prerequisites"].append(left)
            elif relation == "common-misconception-of":
                misconception_id = f"{left}_of_{right}"
                misconceptions[misconception_id] = {
                    "affects": right,
                    "description": row.get("source_text", "Candidate misconception from C1"),
                }

    return {"concepts": concepts, "misconceptions": misconceptions,
            "_note": "C1 relations are unverified candidates; do not treat them as final evidence."}


def _concept_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")

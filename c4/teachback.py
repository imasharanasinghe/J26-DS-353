"""The teach-back exam, Mode 1 (written).

For each lecture the student is asked to explain some concepts and must include named graph
terms. Scoring, in order:

1. coverage      are the required graph concepts present?
2. claim check   are the student's statements true against the graph? (the existing C4 verifier)
3. novice test   a knowledge-restricted novice that sees only the text takes the hidden test
4. evidence      score per (concept, Bloom level), with item counts, for C2

The score is formative evidence for learning support. It is not a grade until the instrument has
passed the validity and fairness checks (``c4.instrument``, and the human pilot).
"""

from __future__ import annotations

import re
from typing import Any

from . import instrument
from .metrics import wilson_interval
from .novice import Novice, graph_universe, split_statements, summarise, take_test
from .pipeline import C4Config, C4Pipeline
from .testbank import build_test

EVIDENCE_SOURCE = "teachback_exam"
SCHEMA = "c4-evidence/1.0"
# A single item is weak evidence. Level scores with fewer items than this are flagged `thin`.
THIN_ITEMS = 2


def make_prompt(kg: dict[str, Any], concept_id: str) -> dict[str, Any]:
    """'Explain X in your own words. Your answer must include Y and Z.'

    The required terms are the concept's direct prerequisites and a named part of its first fact,
    all taken from the graph.
    """
    concepts = kg["concepts"]
    concept = concepts[concept_id]
    name = concept.get("name", concept_id)
    required = [concepts[p].get("name", p) for p in concept.get("prerequisites", []) if p in concepts]
    return {
        "concept": concept_id,
        "text": (f"Explain what {name} is in your own words."
                 + (f" Your answer must include: {', '.join(required)}." if required else "")),
        "required_concepts": [p for p in concept.get("prerequisites", []) if p in concepts],
        "bloom_targets": [1, 2],
    }


def lecture_prompts(kg: dict[str, Any], concept_ids: list[str]) -> list[dict[str, Any]]:
    return [make_prompt(kg, concept_id) for concept_id in concept_ids]


def coverage(kg: dict[str, Any], text: str, concept_ids: list[str]) -> dict[str, Any]:
    """Which of the required graph concepts the text mentions (longest-match, as the verifier)."""
    pipeline = C4Pipeline(kg)
    mentioned = set(pipeline._mentioned_concepts(text))
    present = [c for c in concept_ids if c in mentioned]
    missing = [c for c in concept_ids if c not in mentioned]
    return {"required": concept_ids, "present": present, "missing": missing,
            "coverage": round(len(present) / len(concept_ids), 4) if concept_ids else None}


def claim_check(kg: dict[str, Any], text: str) -> dict[str, Any]:
    """Factual labels of the student's own sentences; contradictions are the diagnostic signal."""
    pipeline = C4Pipeline(kg, C4Config(check_cognitive=False, rewrite=False))
    rows = pipeline.factual_check(text)
    counts = {label: sum(row["factual_status"] == label for row in rows)
              for label in ("ENTAILED", "CONTRADICTED", "UNSUPPORTED")}
    return {"claims": rows, "counts": counts,
            "contradicted": [row["text"] for row in rows if row["factual_status"] == "CONTRADICTED"]}


def evidence_messages(student: str, results: list[dict[str, Any]], graph_version: str) -> list[dict[str, Any]]:
    """One message per (student, concept, Bloom level), the C2 evidence format."""
    messages = []
    table = summarise(results, "concept_bloom")
    for (concept, bloom), row in sorted(table.items()):
        interval = wilson_interval(round(row["score"] * row["items"]), int(row["items"]))
        messages.append({
            "schema": SCHEMA, "student": student, "concept": concept, "bloom": bloom,
            "score": round(row["score"], 4), "items": int(row["items"]),
            "ci95": [round(interval[0] / 100, 4), round(interval[1] / 100, 4)] if interval else None,
            "thin": row["items"] < THIN_ITEMS,
            "source": EVIDENCE_SOURCE, "weight": "provisional", "graph_version": graph_version,
        })
    return messages


def score_exam(
    kg: dict[str, Any],
    novice: Novice,
    student: str,
    text: str,
    concept_ids: list[str],
    graph_version: str = "unversioned",
    required: list[str] | None = None,
) -> dict[str, Any]:
    """Run the Mode 1 pipeline on one student's explanation of ``concept_ids``."""
    items = build_test(kg, concept_ids)
    if not items:
        raise ValueError("no test items for these concepts")
    cover = coverage(kg, text, required if required is not None else concept_ids)
    claims = claim_check(kg, text)
    results = take_test(novice, text, items)
    depth = instrument.depth(text, kg, results, items)
    levels = summarise(results, "bloom")
    return {
        "student": student, "novice": novice.name, "concepts": concept_ids,
        "words": len(re.findall(r"\w+", text)), "statements": len(split_statements(text)),
        "coverage": cover, "claim_check": claims,
        "novice_test": {"overall": summarise(results)["all"],
                        "by_bloom": {str(level): row for level, row in sorted(levels.items())},
                        "items": results},
        "depth": depth,
        "evidence": evidence_messages(student, results, graph_version),
        "flags": flags(cover, claims, depth, summarise(results)["all"]),
        "use": "formative evidence only; not a grade until validity and fairness are shown",
    }


def flags(cover: dict[str, Any], claims: dict[str, Any], depth: dict[str, Any],
          overall: dict[str, float]) -> list[str]:
    out = []
    if cover["missing"]:
        out.append("missing required concepts: " + ", ".join(cover["missing"]))
    if claims["contradicted"]:
        out.append(f"{len(claims['contradicted'])} statement(s) contradict a known-false statement in the graph")
    if depth["untraced"]:
        out.append(f"{depth['untraced']} correct novice answer(s) are not traceable to the text and are discounted")
    if overall["abstained"] > 0.5:
        out.append("the novice could not answer most items from this text (thin explanation)")
    return out


def cohort_report(kg: dict[str, Any], novice: Novice, texts: dict[str, str],
                  concept_ids: list[str]) -> dict[str, Any]:
    """Score several students and give the lecturer a per-concept view (formative)."""
    rows = {student: score_exam(kg, novice, student, text, concept_ids) for student, text in texts.items()}
    per_concept: dict[str, list[float]] = {}
    for row in rows.values():
        for evidence in row["evidence"]:
            per_concept.setdefault(evidence["concept"], []).append(evidence["score"])
    return {"students": rows,
            "concept_means": {c: round(sum(v) / len(v), 4) for c, v in per_concept.items()}}

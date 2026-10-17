"""Prompts for the LLM proposer, and a tolerant parser for its JSON answers."""
from __future__ import annotations

import json
import re

from .edits import hint
from .schemas import Step, path_str

STEP_FORMAT = (
    "Each step is a string:\n"
    '  "learn:<concept_id>"         teach the concept\n'
    '  "probe:<concept_id>"         a quick check question on a concept the learner probably knows\n'
    '  "remediate:<misconception_id>" fix a wrong belief before continuing\n'
)


def _context_block(ctx) -> str:
    kg, fr, lr, cfg = ctx.kg, ctx.frontier, ctx.learner, ctx.cfg
    rel = sorted(set(fr.required) | {p for c in fr.required for p in kg.prereqs(c)})
    concepts = "\n".join(
        f"- {c}: {kg.name(c)} | difficulty {kg.difficulty(c)} | needs {kg.prereqs(c) or '-'}"
        f" | learner mastery {lr.m(c):.2f}, model uncertainty {lr.u(c):.2f}"
        for c in rel)
    mis = "\n".join(f"- {m}: {kg.misconceptions[m]['description']} (affects {kg.misconception_target(m)})"
                    for m in fr.misconceptions) or "- none"
    return (
        f"TARGET: {fr.target} ({kg.name(fr.target)})\n\n"
        f"CONCEPTS (only these may be used):\n{concepts}\n\n"
        f"The learner already knows a concept when mastery >= {cfg.mastery_threshold}.\n"
        f"Concepts the learner must still learn: {', '.join(fr.required)}\n"
        f"Known but uncertain (probe before relying on them): {', '.join(fr.probe_candidates) or 'none'}\n"
        f"Active misconceptions:\n{mis}\n"
        f"Suggested starting order (a hint, not a rule): {', '.join(ctx.bias)}\n"
    )


def proposal_prompt(ctx, k: int):
    system = ("You plan learning paths for a data-structures course. You must follow good "
              "teaching order. Answer with JSON only.")
    user = (
        _context_block(ctx) +
        "\nRULES:\n"
        "1. Every prerequisite comes before the concept that needs it.\n"
        f"2. Climb difficulty gradually: never more than {ctx.cfg.zpd_width} level above the hardest thing learned so far.\n"
        "3. Do not teach what the learner already knows. No duplicates. End with the target.\n"
        "4. Add a probe step before using an uncertain concept.\n"
        "5. Add a remediate step before any concept affected by an active misconception.\n\n"
        + STEP_FORMAT +
        f'\nWrite {k} different valid paths. Reply exactly as: {{"paths": [["learn:a", "..."], ...]}}'
    )
    return system, user


def repair_prompt(ctx, path, violations):
    system = ("You fix learning paths. Change ONLY the steps named in the errors. Keep every other "
              "step in the same order. Answer with JSON only.")
    errs = "\n".join(f"- {v}  ->  {hint(v)}" for v in violations)
    user = (
        _context_block(ctx) +
        f"\nCURRENT PATH:\n{json.dumps([str(s) for s in path])}\n\n"
        f"CHECKER ERRORS (exact faults, with the fix to apply):\n{errs}\n\n"
        + STEP_FORMAT +
        '\nReply exactly as: {"paths": [[...fixed path...]]}'
    )
    return system, user


def _norm(item: str) -> str:
    s = str(item).strip()
    return s if ":" in s else f"learn:{s}"


def parse_paths(text: str) -> list[list[Step]]:
    """Pull {"paths": [[...]]} out of the reply, even if wrapped in prose or ``` fences."""
    if not text:
        return []
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return []
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    raw = data.get("paths") or ([data["path"]] if "path" in data else [])
    out = []
    for p in raw:
        if isinstance(p, list):
            out.append([Step.parse(_norm(x)) for x in p])
    return out


__all__ = ["proposal_prompt", "repair_prompt", "parse_paths", "path_str"]

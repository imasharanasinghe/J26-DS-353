"""Layered, versioned graph with gated proposals (Phase 5, small demo).

"Dynamic" here means layers, versions and proposals, not a graph that rewrites itself:

1. base graph          department-level concepts and prerequisites; changes rarely
2. lecturer overlay    per lecturer and offering: add or hide concepts, add or remove edges,
                       emphasis, terminology. Inherits from the base.
3. audited confidence  per offering, from the Graph Auditor (``c4.auditor``)

Every automatic change (audit result, transcript diff) is a **proposal**. A lecturer approves or
rejects it. Approved proposals become a new version with a changelog entry. The graph is **frozen**
for each block so students are not assessed against a moving target.
"""

from __future__ import annotations

import copy
import itertools
from dataclasses import dataclass, field
from typing import Any

PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
KINDS = ("add_edge", "remove_edge", "reverse_edge", "lower_confidence", "add_concept", "mark_not_covered",
         "split", "merge", "rename")


class GraphError(ValueError):
    pass


class FrozenError(GraphError):
    pass


@dataclass
class Proposal:
    id: int
    kind: str
    payload: dict[str, Any]
    source: str                       # audit | transcript_diff | lecturer
    evidence: str = ""
    status: str = PENDING
    decided_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "kind": self.kind, "payload": self.payload, "source": self.source,
                "evidence": self.evidence, "status": self.status, "decided_by": self.decided_by}


def _edges(concepts: dict[str, Any]) -> set[tuple[str, str]]:
    return {(p, c) for c, v in concepts.items() for p in v.get("prerequisites", [])}


def _has_cycle(concepts: dict[str, Any]) -> bool:
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        for p in concepts[node].get("prerequisites", []):
            if p in concepts and visit(p):
                return True
        state[node] = 2
        return False

    return any(visit(c) for c in concepts)


def resolve(base: dict[str, Any], overlay: dict[str, Any] | None = None,
            edge_confidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Effective graph = base + overlay + audited confidence. Inputs are not modified."""
    graph = copy.deepcopy(base)
    concepts = graph["concepts"]
    overlay = overlay or {}
    for concept_id, concept in overlay.get("add_concepts", {}).items():
        concepts[concept_id] = copy.deepcopy(concept)
    for a, b in overlay.get("remove_edges", []):
        if b in concepts and a in concepts[b].get("prerequisites", []):
            concepts[b]["prerequisites"].remove(a)
    for a, b in overlay.get("add_edges", []):
        if a in concepts and b in concepts and a not in concepts[b].setdefault("prerequisites", []):
            concepts[b]["prerequisites"].append(a)
    for concept_id in overlay.get("not_covered", []):
        if concept_id in concepts:
            concepts[concept_id]["covered"] = False
    for concept_id, weight in overlay.get("emphasis", {}).items():
        if concept_id in concepts:
            concepts[concept_id]["emphasis"] = weight
    for concept_id, terms in overlay.get("terms", {}).items():
        if concept_id in concepts:
            concepts[concept_id]["terms"] = list(terms)
    if _has_cycle(concepts):
        raise GraphError("the overlay creates a prerequisite cycle")
    if edge_confidence:
        graph["edge_confidence"] = copy.deepcopy(edge_confidence)
    return graph


def migrate_mastery(mastery: dict[str, float], uncertainty: dict[str, float], change: dict[str, Any],
                    extra_uncertainty: float = 0.15) -> dict[str, Any]:
    """Move a learner's mastery across a concept change (stable ids).

    split   children inherit the parent's mastery with added uncertainty
    merge   the merged concept takes the lower mastery and the combined (larger) uncertainty
    rename  mastery follows the concept unchanged
    new edge  no demotion: the concept is listed for a re-check instead
    """
    m, u = dict(mastery), dict(uncertainty)
    recheck: list[str] = []
    kind = change["kind"]
    if kind == "split":
        parent = change["concept"]
        for child in change["into"]:
            m[child] = m.get(parent, 0.0)
            u[child] = min(1.0, u.get(parent, 1.0) + extra_uncertainty)
        m.pop(parent, None)
        u.pop(parent, None)
    elif kind == "merge":
        parts = [c for c in change["concepts"] if c in m]
        if parts:
            m[change["into"]] = min(m[c] for c in parts)
            u[change["into"]] = min(1.0, max(u.get(c, 1.0) for c in parts) + 0.05)
        for c in change["concepts"]:
            if c != change["into"]:
                m.pop(c, None)
                u.pop(c, None)
    elif kind == "rename":
        old, new = change["concept"], change["into"]
        if old in m:
            m[new], u[new] = m.pop(old), u.pop(old, 1.0)
    elif kind == "add_edge":
        recheck.append(change["edge"][1])
    else:
        raise GraphError(f"no migration rule for {kind}")
    return {"mastery": m, "uncertainty": u, "recheck": recheck}


class GraphStore:
    """Versions, a proposal queue and a changelog for one offering."""

    def __init__(self, base: dict[str, Any], offering: str = "offering") -> None:
        self.base = copy.deepcopy(base)
        self.offering = offering
        self.overlay: dict[str, Any] = {"add_concepts": {}, "add_edges": [], "remove_edges": [],
                                        "not_covered": [], "emphasis": {}, "terms": {}}
        self.edge_confidence: dict[str, Any] = {}
        self.proposals: list[Proposal] = []
        self.changelog: list[dict[str, Any]] = []
        self.frozen_block: str | None = None
        self._ids = itertools.count(1)
        self._version = 0
        self._commit("initial", [])

    # ---- reading
    @property
    def version(self) -> str:
        return f"{self.offering}-v{self._version}"

    def graph(self) -> dict[str, Any]:
        graph = resolve(self.base, self.overlay, self.edge_confidence)
        graph["graph_version"] = self.version
        return graph

    # ---- proposals (anyone / any process may propose; nothing changes until a lecturer approves)
    def propose(self, kind: str, payload: dict[str, Any], source: str, evidence: str = "") -> Proposal:
        if kind not in KINDS:
            raise GraphError(f"unknown proposal kind {kind}")
        proposal = Proposal(next(self._ids), kind, payload, source, evidence)
        self.proposals.append(proposal)
        return proposal

    def propose_from_audit(self, report: dict[str, Any]) -> list[Proposal]:
        kinds = {"Contested": "lower_confidence", "Unsupported": "remove_edge", "Reversed": "reverse_edge",
                 "Missing": "add_edge"}
        made = []
        for row in report["proposals"]:
            kind = kinds.get(row["status"])
            if kind:
                made.append(self.propose(kind, {"edge": row["edge"]}, "audit", row["evidence"]))
        return made

    def propose_from_transcript_diff(self, previous: set[str], current: set[str], known: set[str]) -> list[Proposal]:
        """Weekly re-read of lecture transcripts: concepts newly mentioned, or no longer mentioned."""
        made = [self.propose("add_concept", {"concept": c}, "transcript_diff", "newly mentioned in this week's transcript")
                for c in sorted(current - previous - known)]
        made += [self.propose("mark_not_covered", {"concept": c}, "transcript_diff", "no longer mentioned")
                 for c in sorted((previous - current) & known)]
        return made

    def decide(self, proposal_id: int, approve: bool, lecturer: str) -> Proposal:
        if not lecturer:
            raise GraphError("a named lecturer must decide")
        proposal = next((p for p in self.proposals if p.id == proposal_id), None)
        if proposal is None:
            raise GraphError(f"no proposal {proposal_id}")
        proposal.status, proposal.decided_by = (APPROVED if approve else REJECTED), lecturer
        return proposal

    # ---- freezing and committing
    def freeze(self, block: str) -> None:
        self.frozen_block = block

    def unfreeze(self) -> None:
        self.frozen_block = None

    def commit(self, label: str = "") -> str:
        """Apply approved proposals as a new version. Refused while the block is frozen."""
        if self.frozen_block:
            raise FrozenError(f"graph is frozen for block {self.frozen_block}; changes wait for the next block")
        approved = [p for p in self.proposals if p.status == APPROVED]
        trial = copy.deepcopy(self.overlay)
        trial_conf = copy.deepcopy(self.edge_confidence)
        for proposal in approved:
            self._apply(proposal, trial, trial_conf)
        resolve(self.base, trial, trial_conf)  # raises on a cycle before anything is kept
        self.overlay, self.edge_confidence = trial, trial_conf
        for proposal in approved:
            proposal.status = "applied"
        return self._commit(label or "approved proposals", approved)

    def _apply(self, proposal: Proposal, overlay: dict[str, Any], confidence: dict[str, Any]) -> None:
        payload = proposal.payload
        if proposal.kind == "add_edge":
            overlay["add_edges"].append(list(payload["edge"]))
        elif proposal.kind == "remove_edge":
            overlay["remove_edges"].append(list(payload["edge"]))
        elif proposal.kind == "reverse_edge":
            a, b = payload["edge"]
            overlay["remove_edges"].append([a, b])
            overlay["add_edges"].append([b, a])
        elif proposal.kind == "lower_confidence":
            a, b = payload["edge"]
            confidence[f"{a}->{b}"] = {"status": "Contested", "n": payload.get("n", 0)}
        elif proposal.kind == "add_concept":
            overlay["add_concepts"][payload["concept"]] = payload.get(
                "definition", {"name": payload["concept"], "difficulty": 3, "prerequisites": []})
        elif proposal.kind == "mark_not_covered":
            overlay["not_covered"].append(payload["concept"])
        else:
            raise GraphError(f"{proposal.kind} proposals change concept ids and are applied by hand in this demo")

    def _commit(self, label: str, applied: list[Proposal]) -> str:
        self._version += 1
        self.changelog.append({"version": self.version, "label": label, "changes": [p.to_dict() for p in applied]})
        return self.version

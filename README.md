# J26-DS-353
# Pedagogy-Typed Knowledge Graphs for Verified Personalized Learning Path Generation

> A Neuro-Symbolic Middleware for Knowledge-Graph-Grounded Personalized Learning Paths with Pedagogy-Aware Verification of LLM Reasoning

---

## Project Overview

Most online learning platforms give every student the same fixed content sequence. LLM-based tutors personalise fluently — but hallucinate facts, skip prerequisites, and provide no way to verify their output.

This research builds a **middleware framework** that combines the best of both worlds. At its core is one shared **pedagogy-typed knowledge graph** — a map of a subject where every connection carries a teaching-specific meaning. This one graph powers four downstream components: knowledge graph construction, student modelling, learning path generation, and explanation generation.

> **One map. Three jobs. Zero disconnected tools.**

---

## System Architecture

```
Raw Course Material (MOOC Transcripts)
            │
            ▼
┌─────────────────────────────┐
│  Component 1 — Build Map    │  ← Member A (IT23189744)
│  LLM Extractor + Verifier   │
│  → Neo4j Knowledge Graph    │
└────────────┬────────────────┘
             │  Pedagogy-Typed KG
    ┌────────┼────────┬─────────────┐
    ▼        ▼        ▼             ▼
┌───────┐  Shared  ┌──────────┐  ┌──────────┐
│  C2   │  Graph   │   C3     │  │   C4     │
│Student│ ───────► │  Path    │─►│ Explain  │
│ Model │          │Generator │  │ Verifier │
└───────┘          └──────────┘  └──────────┘
            │
            ▼
      REST API Middleware
            │
            ▼
   LMS / MOOC / Training Platform
```

---

## Team — J26-DS-353

| Member | ID | Component | Role |
|---|---|---|---|
| Ranasinghe R.A.I.K | IT23189744 | Component 1 | Pedagogy-Aware KG Construction |
| Sawandi D.E.P | IT23229716 | Component 2 | GNN Student Modelling |
| Chamuditha H.V.C | IT23288744 | Component 3 | Neuro-Symbolic Path Generation |
| Amarasinghe S.A.R.U | IT23216778 | Component 4 | Bloom-Aware Explanation Faithfulness |

**Supervisor:** Prof. Nuwan Kodagoda  
**Co-Supervisor:** Mr. Jeewaka Perera  
**Research Group:** CoEAI — Centre of Excellence for AI  
**Specialisation:** Data Science (DS)

---

## The Four Components

### Component 1 — Pedagogy-Aware Knowledge Graph Construction
Reads raw course material and constructs a typed knowledge graph using an LLM extractor and a symbolic rule-based verifier. Introduces four first-class teaching edge types absent from standard ontologies.

### Component 2 — Uncertainty-Aware GNN Student Modelling
Models each learner's mastery and calibrated uncertainty per concept using the KG as a structural prior. Solves the cold-start problem via prerequisite propagation.

### Component 3 — Neuro-Symbolic Learning Path Generation
LLM proposes a path → symbolic critic checks it against the KG → typed violations returned → only the broken step is fixed. Topological-sort fallback guarantees a safe path always.

### Component 4 — Bloom-Level-Aware Explanation Faithfulness
Checks every claim in an LLM-generated explanation against: (1) factual entailment from the KG and (2) cognitive appropriateness against the learner's Bloom ceiling.

---

## Key References

1. Chu et al., "LLM Agents for Education," arXiv:2503.11733, 2025.
2. "Personalized Learning Path Recommendation Based on KGs: A Survey," Electronics, vol. 15, 2026.
3. "EDUKG: A Heterogeneous Sustainable K-12 Educational KG," 2022.
4. Nakagawa et al., "Graph-based Knowledge Tracing," IEEE/WIC/ACM, 2019.
5. Yang et al., "GIKT," ECML-PKDD, 2020.

---

## License

IT4010 Final Year Research Project — SLIIT, Sri Lanka Institute of Information Technology.

---

*Built by Group J26-DS-353 · CoEAI · SLIIT · 2026*

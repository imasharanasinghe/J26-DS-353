# J26-DS-353
# 🧠 Pedagogy-Aware Knowledge Graph Construction
### Component 1 — IT4010 Research Project | J26-DS-353 | SLIIT

> **One shared map. Three downstream jobs.**
> This component builds the pedagogy-typed knowledge graph that powers the entire research framework.

---

## 📌 What This Does

This component reads raw educational content — lecture transcripts, textbooks, and course material — and automatically constructs a **pedagogy-typed knowledge graph** using a hybrid LLM + symbolic verifier pipeline.

Unlike ordinary concept maps, every edge in this graph carries a **teaching-specific meaning**:

| Edge Type | Meaning |
|---|---|
| `PREREQUISITE_OF` | Concept A must be learned before Concept B |
| `COGNITIVE_LOAD` | How mentally demanding a concept is (computed from prerequisite depth) |
| `BLOOM_LEVEL` | Highest Bloom's taxonomy level a concept is assessed at |
| `COMMON_MISCONCEPTION_OF` | Concept A is frequently confused when learning Concept B |

The verified graph is stored in **Neo4j** and serves as the shared backbone for three downstream components — student modeling (C2), path generation (C3), and explanation verification (C4).

---

## 🗂️ Project Structure

```
component1/
│
├── data/                   # Raw MOOC datasets (Princeton + UC San Diego)
├── extraction/             # Concept & relation extraction using LLM
│   ├── concept_extractor.py
│   ├── concept_normaliser.py
│   └── relation_extractor.py
├── verifier/               # Symbolic rule-based verifier
│   ├── symbolic_verifier.py
│   └── misconception_list.py
├── neo4j/                  # Graph database integration
│   └── graph_builder.py
├── gold_corpus/            # Human-annotated evaluation data
│   ├── gold_corpus_selector.py
│   ├── annotator1.csv
│   ├── annotator2.csv
│   └── gold_standard.csv
├── evaluation/             # Precision, Recall, F1 scoring
│   └── evaluator.py
├── outputs/                # Generated graphs, results, exports
├── data_loader.py
├── data_cleaner.py
├── .env.example
└── requirements.txt
```

---

## 🔄 Pipeline Overview

```
📚 Raw Course Material (MOOC Transcripts)
           │
           ▼
   🤖 LLM Concept Extractor
   (GPT-4 — proposes concepts and typed edges)
           │
           ▼
   ✅ Symbolic Rule Verifier
   (Anti-cycle · Bloom consistency · Misconception whitelist)
           │
           ▼
   🔢 Cognitive Load Calculator
   (Prerequisite depth count — deterministic)
           │
           ▼
   💾 Neo4j Knowledge Graph
   (Nodes = Concepts · Edges = Typed Relations)
           │
           ▼
   📊 Gold Corpus Evaluation
   (Precision · Recall · F1 per edge type · Cohen's Kappa)
```

---

## 📦 Datasets Used

| Dataset | Source | Records | Domain |
|---|---|---|---|
| Princeton Algorithms | Coursera MOOC Captions | 59 lecture transcripts | Algorithms (Sedgewick) |
| UC San Diego DSA | Coursera MOOC Captions | 263 lecture transcripts | Data Structures & Algorithms |

> Raw text only — no pre-labelled edges. All relations are extracted and computed by this pipeline.

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/component1-kg.git
cd component1-kg
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Set up environment variables

Copy `.env.example` to `.env` and fill in your keys:
```
OPENAI_API_KEY=sk-your-key-here
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
```

### 4. Start Neo4j
Download [Neo4j Desktop](https://neo4j.com/download/), create a local instance, and start it.

---

## 🚀 Run the Pipeline

Run each phase in order:

```bash
# Phase 2 — Load and prepare data
python data_loader.py

# Phase 3 — Extract concepts
python extraction/concept_extractor.py
python extraction/concept_normaliser.py

# Phase 4 — Extract relations
python extraction/relation_extractor.py

# Phase 5 — Verify edges
python verifier/symbolic_verifier.py

# Phase 6 — Compute cognitive load
python extraction/cognitive_load.py

# Phase 7 — Build Neo4j graph
python neo4j/graph_builder.py

# Phase 8 — Select gold corpus sentences
python gold_corpus/gold_corpus_selector.py

# Phase 9 — Evaluate
python evaluation/evaluator.py
```

---

## 📊 Evaluation Metrics

| Metric | What it measures |
|---|---|
| **Precision** | Of edges extracted, how many were correct |
| **Recall** | Of all correct edges, how many were found |
| **F1 Score** | Harmonic mean of precision and recall |
| **Cohen's Kappa** | Inter-annotator agreement on gold corpus |

All metrics are computed **per edge type** — not as a single aggregate score.

---

## 🔬 Novelty

> This is what makes Component 1 different from existing educational knowledge graphs:

- ✅ **Four pedagogy-typed edges** absent from standard ontologies (ACM CCS, IEEE LOM)
- ✅ **Hybrid pipeline** — LLM proposes, symbolic rules verify (not LLM-only)
- ✅ **Deterministic cognitive load** — computed from graph structure, not AI-estimated
- ✅ **Per-type evaluation** against a hand-annotated gold corpus with inter-annotator agreement
- ✅ **One shared graph** that feeds three downstream research components

---

## 🏗️ Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| OpenAI GPT-4 | Concept & relation extraction |
| Neo4j | Graph database storage |
| spaCy | NLP preprocessing |
| NetworkX | Graph analysis & cycle detection |
| scikit-learn | Evaluation metrics |
| Matplotlib | Graph visualisation |

---

## 👤 Author

**Ranasinghe R.A.I.K** — IT23189744
Member A · Component 1
BSc (Hons) Data Science · SLIIT
Research Group J26-DS-353

---

## 📄 License

This project is part of an academic research project at SLIIT.
For research use only.

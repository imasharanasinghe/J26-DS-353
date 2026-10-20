# Component 1: Pedagogy-Aware Knowledge Graph Construction

This component builds a data-structures-and-algorithms knowledge graph from Princeton course captions and a Chinese MOOC dataset. The pipeline extracts concepts and candidate prerequisite, Bloom-level, and misconception relations, verifies them symbolically, and stores verified relations in Neo4j.

## Contents

- `data/raw/` — source captions and MOOC dataset files. `concept.json` is stored with Git LFS.
- `data/processed/chunks.csv` — overlapping text chunks generated from captions.
- `src/stage0_mooc_dataset.py` — translates MOOC concepts and writes `outputs/concept_nodes.csv`.
- `src/stage1_prepare.py` — cleans captions and creates text chunks.
- `src/stage2_concepts.py` — extracts caption concepts.
- `src/stage3_relations.py` — extracts candidate prerequisite, Bloom-level, and misconception relations.
- `src/stage4_verifier.py` — rejects self-loops, invalid misconception pairs, invalid Bloom levels, and prerequisite cycles.
- `src/stage5_storage.py` — computes cognitive-load values and stores verified data in Neo4j.
- `test_connection.py` — checks Neo4j connectivity.
- `outputs/` — reproducible intermediate and verified CSV snapshots.
- `gold_corpus/` — location for evaluation annotations.

## Setup

Install Git LFS before cloning so the MOOC concept dataset can be downloaded. Run commands from this directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
Copy-Item .env.example .env
```

Edit `.env` locally with your own Neo4j settings. Never commit `.env` or share its values.

## Run the pipeline

```powershell
python src\stage1_prepare.py
python src\stage2_concepts.py
python src\stage0_mooc_dataset.py
python src\stage3_relations.py
python src\stage4_verifier.py
python src\stage5_storage.py
```

The default extraction sample is 100 chunks. Stage 0 reads the MOOC files from `data/raw/`; stage 1 writes `data/processed/chunks.csv`; stages 0–4 write CSVs under `outputs/`. Stage 2 requires the `en_core_web_sm` spaCy model. Run scripts from this directory because they use relative paths.

Relation extraction uses heuristics and domain-knowledge seeds; verified output should still be reviewed before being treated as ground truth. **Stage 5 deletes all nodes and relationships in the configured Neo4j database before writing the graph.** Use a dedicated database and confirm its contents are backed up before running it.

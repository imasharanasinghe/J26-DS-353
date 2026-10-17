# Component 2 — Uncertainty-Aware GNN Student Modelling

Estimates, for every concept (skill), a learner's **mastery** (probability of answering correctly) and an
**uncertainty** (spread over 30 Monte Carlo Dropout passes), using a prerequisite graph as structural prior.
Status: working prototype trained and evaluated on ASSISTments 2009-10 (skill builder). The graph used so far is a
**data-derived placeholder**; Component 1's pedagogy-typed graph plugs in via `--graph` and the same tests can be rerun.

## Data (not included)
ASSISTments 2009-2010 skill builder, corrected + collapsed version (`skill_builder_data_corrected_collapsed.csv`).
Place it in this folder. Cleaning (in `c2_assist_data.py`): drop rows without a skill label, keep correct in {0,1},
sort by time, keep learners with >= 25 answers (cap 300), split **by learner** 70/15/15.
`python c2_data_summary.py --data <csv>` prints the exact numbers.

## Setup
```
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt     # torch 2.2.2 pinned for Intel Macs; newer torch works elsewhere
```

## Scripts
| Script | Purpose |
|---|---|
| `c2_train_assistments.py` | Train GNN, no-graph ablation, DKT baseline; AUC/ECE/Brier, cold-start table, MC-pass sweep (`--mc_sweep`), `--features v1/v2`, `--seed` |
| `c2_mc_eval.py` | MC Dropout evaluation: dropout rate, single pass vs MC, 4 uncertainty measures, error detection, within-probability-band test, cold-start check |
| `c2_seen_unseen.py` | Graph vs no graph on attempted vs never-attempted skills |
| `c2_demo.py` | `--train` saves the final model; `--list`, `--learner <id> --k 20` shows one unseen learner's mastery + uncertainty |
| `c2_data_summary.py` | Dataset and cleaning report |
| `c2_model.py`, `c2_data.py`, `c2_assist_data.py`, `c2_dkt.py` | Model, features, loading/graph, DKT baseline |

Component 1 graph: CSV with columns `prereq,skill` (dataset skill ids), then add `--graph c1_edges.csv`.

## Results so far (test = 281 unseen learners, 3 seeds, default dropout 0.25, 30 passes)
| Model | AUC | ECE | Brier |
|---|---|---|---|
| GNN (graph) | 0.727 ± 0.001 | 0.019 ± 0.007 | 0.1982 |
| Same network, no graph | 0.723 ± 0.001 | 0.016 ± 0.002 | 0.1992 |
| DKT (LSTM) | 0.727 ± 0.002 | 0.040 ± 0.002 | 0.1998 |

## Findings and limitations (honest status)
- The graph gives a small, consistent gain over the no-graph network (+0.004 AUC, positive in 3/3 seeds), mostly on
  skills the learner already attempted. On never-attempted skills the gain is small and inconsistent (+0.002; one seed negative).
  This used the placeholder graph, so the cold-start benefit of prerequisite propagation is **not yet established**.
- 30-pass MC Dropout gives the same accuracy and calibration as a single deterministic pass. The pass count mainly affects
  estimate stability (mastery wobble 0.012 at 10 passes, 0.007 at 30, 0.004 at 100).
- MC uncertainty is only weakly informative: error-detection AUROC 0.56 at best (dropout 0.1) vs 0.65 for a
  probability-only baseline; it does not rise for learners with less history (std 0.0318 at 5 answers vs 0.0316 at 40).
  Lower dropout (0.1) gave the best calibration (ECE 0.0115) and the best uncertainty.
- Seeds vary model initialisation only; the learner split is fixed. Mastery is a proxy learned from next-answer prediction.

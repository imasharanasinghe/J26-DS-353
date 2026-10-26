# NEW1: Teachability, a revised Component 4 scope

**Teachability: measuring and optimising how well understanding transfers between minds**

J26-DS-353, Component 4 (Amarasinghe S A R U, IT23216778)
Status: **proposal draft, not yet approved by the supervisor.** Nothing in this file is implemented yet. Written after the PP1 result (22 October 2026), where the panel asked for a much deeper, more inventive scope.

---

## 1. Why the scope changes

The PP1 panel said the four components together amounted to roughly one normal final-year research component, and asked for something new and much deeper in each. C4 today is a well-built verifier: it splits an LLM explanation into claims, checks them against the knowledge graph and the learner's state, and repairs what fails. That is an engineering result. It writes and checks text, which any LLM pipeline can do.

The revised C4 keeps the verifier as a measurement instrument and asks a new, scientific question:

> **When one mind explains something to another, how much understanding actually transfers, can we measure it, and what makes it transfer better?**

## 2. The central idea

An explanation can be *correct* and still *not teach*. The existing verifier measures correctness. This proposal adds a second, independent axis, **teachability**, and then studies it.

| | Transfers (high teachability) | Does not transfer (low teachability) |
|---|---|---|
| **Correct** (passes the verifier) | Good explanation | **Correct but untransferable** (the new, interesting case) |
| **Incorrect** (fails the verifier) | Convincing but wrong (dangerous) | Wrong and confusing |

## 3. Components of the contribution

### 3.1 The teachability score (the measurement tool)

A **knowledge-restricted AI novice** knows only what is in its restricted knowledge state (for example, the concepts a real learner has not yet mastered are removed or suppressed). It reads an explanation, then takes a short test whose items are tagged by Bloom level. Its score is the explanation's teachability, reported per Bloom level.

Required validation, because a score from a leaky model proves nothing:
- **Leakage test:** before reading any explanation, the novice must fail items on the restricted concepts.
- **Discrimination test:** controlled explanations (complete, missing a prerequisite step, shuffled, subtly wrong, no explanation) must be ranked in the expected order.
- **Validity test:** compare novice scores with a small group of real beginners.
- **Comparison with the verifier:** teachability should capture something the correctness verifier does not.

### 3.2 Discovery 1: explanation survivability

Run A -> B -> C teaching chains (a telephone game): one mind explains to the next, which explains to the next. Measure how much meaning survives each hop.

Questions: which explanation styles (analogy first, worked example first, formal definition first, misconception first) survive retelling, which collapse, and does this depend on the Bloom level being taught?

### 3.3 Discovery 2: the tutor-tutee distance and cognitive chemistry

Experts are often poor teachers (the curse of knowledge); near-peers are often better.

Questions: is there an optimal knowledge distance between a tutor and a tutee, how large is it, does it depend on the concept and Bloom level, and which pairings and groups produce the largest gains for both people? Study first in simulation, then confirm in a small human pilot. Output: a measured quantity and a pairing method.

### 3.4 Application: curse-of-knowledge report (for teachers)

From the knowledge graph, find every prerequisite an explanation silently assumes, and compare against what a class or learner has mastered. The teacher sees, for example: "this explanation assumes four things 60% of your class has not yet learned".

### 3.5 Stretch experiments (only if time remains)

- **Convince the stubborn AI:** the student must change the mind of an AI that holds a plausible misconception taken from the graph's known-false list. Success measures the Evaluate and Analyse levels.
- **Question depth:** classify the depth of the questions students ask, as a measure of cognitive level and a map of what a class is confused about.

## 4. Research questions

- **RQ1.** Can a knowledge-restricted novice produce a valid, discriminating teachability score, and does it capture something that factual correctness alone does not?
- **RQ2.** Which explanation styles survive repeated retelling, and does this depend on the Bloom level?
- **RQ3.** Is there an optimal tutor-tutee knowledge distance, and does matching on it improve learning for both people compared with random pairing?
- **RQ4.** Can the unstated-prerequisite report predict where a real class struggles?

The earlier trajectory idea from PP1 (raise the learner's Bloom level over time) is kept: teachability is measured per Bloom level, and the progression policy chooses which level to transfer next.

## 5. What is reused from the current C4

| Existing | Reused as |
|---|---|
| Claim extraction, graph verifier (`c4/pipeline.py`) | The correctness axis; also the check that a tutor's explanation is factually sound |
| Bloom estimator and labelled items (`c4/bloom.py`, `c4/data/bloom_items.json`) | Tagging transfer-test items by Bloom level |
| Progression policy (`c4/progression.py`) | Choosing the next Bloom level to transfer |
| Simulated learners (`c4/simulation.py`) | Seed for simulated tutors, tutees and groups |
| Web workbench (`c4/web/`) | The demo surface; add the novice, chain and report views |
| Stress test and results (`c4/results/`) | Baseline and method for the controlled-explanation experiments |
| Mock C1/C2/C3 fixtures (`c4/data/`) | Inputs for the first phases; no upstream change is required |

## 6. Plan, in priority order

| Phase | Deliverable | Humans needed | Rough effort* |
|---|---|---|---|
| 1. Core (must-have) | Knowledge-restricted novice, teachability score, leakage and discrimination validation | No | 3-4 weeks |
| 2. Discovery 1 (must-have) | Survivability chains and the style-by-Bloom result | No | 2 weeks |
| 3. Discovery 2 (should-have) | Tutor-tutee distance and cognitive chemistry in simulation, then a small human pilot (about 20-30 students) | Yes, for the pilot | 3-4 weeks plus recruitment |
| 4. Application (nice-to-have) | Curse-of-knowledge report | No | 1-2 weeks |
| Stretch | Stubborn AI, question depth | Optional | Only if time remains |

*Guesses for one person working part-time, not commitments. The real deadline is not known and must be fitted in.

**Minimum viable thesis:** phases 1 and 2 done well, phase 3 in simulation with a human pilot, phase 4 if time allows.

## 7. Risks and limits (state these before the panel does)

1. **The novice must be believable.** A small local model (Qwen3 4B) may leak knowledge it should not have. Leakage tests are mandatory, and a stronger model may be needed for final runs. Without validation against real beginners the score is only a model output.
2. **Simulated discoveries are about the simulator.** Phases 2 and 3 become claims about people only if the pilot confirms them.
3. **The human pilot needs consent or ethics approval and enough participants.** If it fails, keep the simulated results and present the pilot as a smaller validation.
4. **Scope.** Depth on phases 1-2 beats shallow coverage of everything.
5. **Novelty is not verified.** Teachable agents, learning-by-teaching systems and peer-tutor matching all exist. The claimed contribution is the teachability metric, the survivability result and the measured tutor-tutee distance. A literature search is required before any novelty claim is made to the panel.
6. **Interfaces.** Mock fixtures are enough to start, but the learner-state and graph schemas must still be agreed with the C1 and C2 owners.

## 8. Open decisions

- Supervisor approval of the revised scope and title.
- The next hard deadline (PP2 / final) to fit the phases to.
- Ethics or consent route for the human pilot.
- Which model plays the novice (local Qwen3 4B vs a stronger hosted model) and the budget for it.
- Whether the verifier remains in the title or becomes a supporting method.

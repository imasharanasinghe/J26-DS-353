# CartoLearn: 2-minute video script and production brief

Hand this whole file to Claude. It is self-contained. Brand assets are in the same folder (`~/Downloads/CartoLEARN/`).

## 0. Brief

Make a silent-capable, voice-over-led video of **1:55 (hard limit 2:00)** for the evaluators of project J26-DS-353 (SLIIT, IT4010 final-year research).

Goal: the evaluator understands **why the project matters**: the problem, who it hurts, and the solution direction. Not a feature tour.

Style: simple, attractive, minimalist, unique. **Nothing is decoration.** Every moving element must show how the system actually works. If an element does not explain something, delete it.

Output: 1920x1080, 30 fps, MP4 (H.264), burned-in captions, plus a `.srt`.

## 1. Brand (fixed, do not change)

| Name | Hex | Use |
|---|---|---|
| Deep Navy | `#0A2540` | Dark background, text on light |
| Ocean | `#135E8C` | Secondary shapes, mid emphasis |
| Sea Blue | `#1596CB` | Primary accent, active elements |
| Shallows | `#3DB8E8` | Highlights, "verified" state, accent on navy |
| Mist | `#F2F8FC` | Light background, text on navy |

- Use only these five colors plus white, with tints of them for secondary states. No red or green. Show "rejected/wrong" with a **broken line, strike-through and a Deep Navy x-mark**, not a warning color.
- Logo files: `Light lockup.png` (light backgrounds), `Dark stacked.png` (dark backgrounds), `App icon.png`, `Mark, black (transparent).png`, `Mark, white (transparent).png`, `Palette.png`.
- The mark is concentric open arcs around a dot, with a line running from the dot to a node. **That dot-line-node is the video's motif.** The wordmark is "Carto" in light weight and "LEARN" in bold. The logo text may change slightly, so always use the files, never retype it.
- Type: Outfit (the palette sheet uses it) for titles and labels, Inter for captions. If neither is available, use any clean geometric sans.

## 2. Visual concept: "one route, four checks"

One continuous line, a learner's route, is drawn across the whole video. It starts as a free-hand dot-to-dot line, and each component adds one **check** to it, until the route is verified from end to end.

- The route is a graph: nodes are concepts (arrays, linked list, tree, heap...). Edges are teaching relationships.
- Light scenes use a Mist background with Deep Navy ink. The problem scene is Mist. The solution scenes alternate Mist and Deep Navy only if the transition is motivated, otherwise stay on Mist.
- The same layout is used in each of the four component scenes (see section 4) so they read as equal. Only the content changes.
- Motion: slow and eased (ease-in-out, 400-700 ms). Lines draw on, nodes fade in. No bounces, particles, glows, stock footage, or music-video cuts.
- Text: at most 8 words on screen at a time, set large, in addition to the captions.
- Audio: calm, neutral, clear voice-over (about 130 words per minute). Optional very quiet ambient pad (-28 LUFS under the voice), or none. A soft tick when a check passes is allowed, and nothing else.

## 3. Equal weight rule

Components 1-4 each get **exactly 20 seconds**, about 45 spoken words, the same three beats (what goes wrong without it / what it does / the proof), the same on-screen label style and the same layout. Do not let one look more important. The problem and the close are shared framing.

| Time | Scene | Length |
|---|---|---|
| 0:00-0:13 | 1. The problem | 13 s |
| 0:13-0:23 | 2. The direction | 10 s |
| 0:23-0:43 | 3. Component 1 | 20 s |
| 0:43-1:03 | 4. Component 2 | 20 s |
| 1:03-1:23 | 5. Component 3 | 20 s |
| 1:23-1:43 | 6. Component 4 | 20 s |
| 1:43-1:55 | 7. Close | 12 s |

## 4. Scene by scene

Fixed layout for scenes 3-6: the route and graph fill the left two thirds. A label sits top-left in the form `01  Build the map` (number in Sea Blue, name in Deep Navy). The proof sits bottom-right as one big figure with a 3-5 word caption. Total on-screen text per scene is under 15 words.

### Scene 1: The problem (0:00-0:13)

**Voice-over (30 words):**
"AI tutors sound certain. But they can skip a prerequisite, invent a fact, or push a learner too far, too fast. And nothing checks them before the learner sees it."

**Visual:** Mist background. A single dot (the learner) at the left, a goal node at the right. An AI draws a smooth line between them, and it looks perfect. As the voice names each fault, the line shows it:
1. "skip a prerequisite": a node on the true route is bypassed (a faint dashed node left behind), and the dot jumps over it.
2. "invent a fact": a node appears along the line with a hollow dashed outline and no connections to the graph.
3. "too far, too fast": the gap between two steps stretches wide.
The dot stalls at the gap. On-screen text: **"Smooth. Confident. Unchecked."**

**Who it hurts (say it by showing it, caption only):** a small caption `Self-directed learners with no tutor to catch it`.

### Scene 2: The direction (0:13-0:23)

**Voice-over (22 words):**
"CartoLearn puts a check between the AI and the learner. One shared map of the subject. Four components. Every output verified."

**Visual:** The logo lockup (`Light lockup.png`) fades in for 1.5 s, then recedes to the corner. A horizontal strip of four equal tiles appears, each a small icon-free diagram: a graph, a node with a halo, a route, a sentence with a tick. Labels: `Build the map`, `Know the learner`, `Plan the path`, `Explain it truthfully`. A thin line beneath all four reads **"The AI suggests. The checker decides."** (this line is the project's own wording from the C3 README).

### Scene 3: Component 1, Build the map (0:23-0:43)

Source: `docs/C1.md`, branch `Component1_KG`.

**Voice-over (43 words):**
"Component one builds the map. It reads lecture transcripts and extracts concepts and four teaching relationships: prerequisite, difficulty, thinking level, and common misconception. A rule checker rejects any link that creates a cycle or a contradiction before it is stored."

**Visual:**
1. Lines of transcript text on the left fade into concept nodes (3-4 nodes).
2. Four edge styles appear in turn, each a different line pattern in the brand blues, with a tiny label: `prerequisite`, `difficulty`, `thinking level`, `misconception`.
3. A proposed edge that would close a loop is drawn, then refused: it breaks into a dashed line and an x-mark, and the graph stays unchanged.

**Proof (bottom-right):** `4` teaching relationship types, caption "that standard ontologies lack".

### Scene 4: Component 2, Know the learner (0:43-1:03)

Source: `docs/C2.md`, branch `component2-gnn-student-model`.

**Voice-over (44 words):**
"Component two models the learner. A graph neural network estimates mastery for every concept, plus how sure it is. It reads the map's prerequisites, so a new learner does not start blind. And its confidence is well calibrated: about half the error of the standard baseline."

**Visual:**
1. The same graph from scene 3, now with a learner dot. Each node fills from the bottom like a gauge (fill height = mastery).
2. A thin halo ring around each node whose width shows uncertainty: wide for a node with few answers, narrow for many.
3. A new learner: all nodes grey. Mastery propagates one hop along a prerequisite edge to its neighbours, filling them partway, with a wide halo.

**Proof:** `0.019 vs 0.040` calibration error, caption "vs standard baseline (ASSISTments)".

### Scene 5: Component 3, Plan the path (1:03-1:23)

Source: `docs/C3.md`, branch `c3_pathplanner`.

**Voice-over (45 words):**
"Component three plans the path. An AI drafts a route to the learner's goal. A symbolic checker tests it against five teaching rules and names exactly which step breaks. Only that step is fixed. Without the checker, 58% of drafted paths broke a rule. With it, none."

**Visual:**
1. The AI draws a route (the same line as scene 1, now on the real graph).
2. Five small rule markers sweep along it. One step turns dashed and a label names the fault, e.g. `MissingPrerequisite: heap needs binary tree`.
3. Only that step is redrawn. The whole route turns Shallows (verified).

**Proof:** `58% -> 0%` of paths broke a rule, caption "36 test cases".

### Scene 6: Component 4, Explain it truthfully (1:23-1:43)

Source: `docs/C4.md`, `PP1.md`, `c4/results/`.

**Voice-over (46 words):**
"Component four explains it. Every sentence is split into claims and checked twice: is it true to the map, and is it right for this learner? Wrong sentences are rewritten, correct ones stay. Then it aims one level higher, so the learner does not just stay put. They grow."

**Visual:**
1. A three-sentence explanation. Each sentence splits into claim chips.
2. Each chip passes two gates drawn as two thin vertical lines: `true to the map`, `right for this learner`. One chip fails, turns dashed with an x-mark, and is rewritten in place. The other two do not move.
3. A six-step ladder (Remember, Understand, Apply, Analyse, Evaluate, Create) appears at the right. The learner dot climbs one rung and a small `Check yourself` card appears at that rung.

**Proof:** `25% -> 0%` of claims were false, caption "controlled stress test".

### Scene 7: Close (1:43-1:55)

**Voice-over (24 words):**
"One map. Four checks. CartoLearn lets AI personalise learning, and makes sure every step is right before a learner takes it."

**Visual:** The full route, now verified end to end in Shallows, reaches the goal node. Cut to the dark stacked logo (`Dark stacked.png`) on Deep Navy. Tagline: **"Every step checked before it's taken."** Below, in small type: `J26-DS-353 · SLIIT · 2026` and the four member names (section 6). Final 3 s: a one-line footnote, `Results are from controlled tests; a human pilot is pending.`

## 5. Full voice-over (about 255 words, about 1:55 with pauses)

> AI tutors sound certain. But they can skip a prerequisite, invent a fact, or push a learner too far, too fast. And nothing checks them before the learner sees it.
>
> CartoLearn puts a check between the AI and the learner. One shared map of the subject. Four components. Every output verified.
>
> Component one builds the map. It reads lecture transcripts and extracts concepts and four teaching relationships: prerequisite, difficulty, thinking level, and common misconception. A rule checker rejects any link that creates a cycle or a contradiction before it is stored.
>
> Component two models the learner. A graph neural network estimates mastery for every concept, plus how sure it is. It reads the map's prerequisites, so a new learner does not start blind. And its confidence is well calibrated: about half the error of the standard baseline.
>
> Component three plans the path. An AI drafts a route to the learner's goal. A symbolic checker tests it against five teaching rules and names exactly which step breaks. Only that step is fixed. Without the checker, fifty-eight percent of drafted paths broke a rule. With it, none.
>
> Component four explains it. Every sentence is split into claims and checked twice: is it true to the map, and is it right for this learner? Wrong sentences are rewritten, correct ones stay. Then it aims one level higher, so the learner does not just stay put. They grow.
>
> One map. Four checks. CartoLearn lets AI personalise learning, and makes sure every step is right before a learner takes it.

## 6. Sources and honesty rules

Every number on screen comes from the repo. Keep these caveats, and do not strengthen the claims:

| Claim | Source | Caveat to keep |
|---|---|---|
| 4 teaching edge types | `docs/C1.md`, `origin/Component1_KG` | C1's evaluation files are empty, so show **no** accuracy figure for C1 |
| Calibration error 0.019 (GNN) vs 0.040 (DKT) | `origin/component2-gnn-student-model` README | ASSISTments, 281 test learners, 3 seeds, placeholder graph (not C1's graph) |
| "A new learner does not start blind" | C2 design | This is the **design**. The C2 README says the cold-start gain is not yet established, so keep the wording as intent, not result |
| 58.3% -> 0% rule violations | `origin/c3_pathplanner`, `docs/pp1_results/` | 36 test cases, GPT-4o proposer, 95% CI 0-9.6% for the 0% |
| 25% -> 0% false claims | `c4/results/RESULTS.md`, `PP1.md` | Controlled stress corpus (84 claims), labels built by recipe, and the same verifier measures the repair, so this shows the repair works as specified and is not independent accuracy |
| Climbs one Bloom level | `PP1.md` | Shown in simulation only. The human pilot is not run and needs ethics approval |

Do not mention the generator model (Qwen or GPT-4o) on screen. Do not claim the four components are integrated end to end: the repo says they are not yet. The video shows the **design and direction**, and the proof figures are per component.

Team names (end card, small): Ranasinghe R.A.I.K (C1), Sawandi D.E.P (C2), Chamuditha H.V.C (C3), Amarasinghe S.A.R.U (C4). Supervisor: Prof. Nuwan Kodagoda.

## 7. Build instructions for Claude

1. Build it as an HTML/SVG animation timeline (GSAP or Remotion are fine, pin exact versions), 1920x1080, driven by the timings in section 3.
2. Reuse **one SVG graph** across scenes 3-6 so the map visibly persists, since that is the whole point.
3. Generate the voice-over with whatever TTS is available, then align scene timings to the actual audio length. If the total exceeds 1:58, trim words, never speed the voice above 150 wpm.
4. Render to MP4 with ffmpeg, burn in captions from the `.srt`.
5. Check frame by frame: no scene over 15 words of on-screen text, every color from the palette, every element tied to the mechanism.
6. Deliver the MP4, the `.srt`, and the project source.

## 8. Things to confirm before rendering

- Have each member sanity-check their own scene's proof figure and caveat.
- If C1's evaluation has results by then, add one proof figure to scene 3 (for example precision/recall/F1) in the same bottom-right slot.
- Confirm whether the evaluators need a voice or only captions, and whether names or a student ID must appear.

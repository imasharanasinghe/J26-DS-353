# CartoLearn: voice-over

Target length 1:55 at about 130 words per minute.

## 1. The problem (0:00-0:13)

AI tutors sound certain. But they can skip a prerequisite, invent a fact, or push a learner too far, too fast. And nothing checks them before the learner sees it.

## 2. The direction (0:13-0:23)

CartoLearn puts a check between the AI and the learner. One shared map of the subject. Four components. Every output verified.

## 3. Component 1: Build the map (0:23-0:43)

Component one builds the map. It reads lecture transcripts and extracts concepts and four teaching relationships: prerequisite, difficulty, thinking level, and common misconception. A rule checker rejects any link that creates a cycle or a contradiction before it is stored.

## 4. Component 2: Know the learner (0:43-1:03)

Component two models the learner. A graph neural network estimates mastery for every concept, plus how sure it is. It reads the map's prerequisites, so a new learner does not start blind. And its confidence is well calibrated: about half the error of the standard baseline.

## 5. Component 3: Plan the path (1:03-1:23)

Component three plans the path. An AI drafts a route to the learner's goal. A symbolic checker tests it against five teaching rules and names exactly which step breaks. Only that step is fixed. Without the checker, fifty-eight percent of drafted paths broke a rule. With it, none.

## 6. Component 4: Explain it truthfully (1:23-1:43)

Component four explains it. Every sentence is split into claims and checked twice: is it true to the map, and is it right for this learner? Wrong sentences are rewritten, correct ones stay. Then it aims one level higher, so the learner does not just stay put. They grow.

## 7. Close (1:43-1:55)

One map. Four checks. CartoLearn lets AI personalise learning, and makes sure every step is right before a learner takes it.

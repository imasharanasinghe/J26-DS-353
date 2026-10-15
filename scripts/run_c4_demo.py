from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from c4 import C4Pipeline


DATA = ROOT / "c4" / "data"


def main() -> None:
    pipeline = C4Pipeline.from_files(DATA / "knowledge_graph.json")
    with (DATA / "verified_path.json").open(encoding="utf-8") as handle:
        path = json.load(handle)
    with (DATA / "learner_state.json").open(encoding="utf-8") as handle:
        learner = json.load(handle)
    explanation = (DATA / "explanation.txt").read_text(encoding="utf-8")
    result = pipeline.run(path, learner, explanation)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()

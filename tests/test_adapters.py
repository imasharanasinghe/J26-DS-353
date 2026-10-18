from pathlib import Path

from c4.adapters import load_c2_learner, load_c1_csv_graph, validate_c3_path


ROOT = Path(__file__).resolve().parents[1]


def test_c2_collection_adapter_selects_learner() -> None:
    data = {"learners": [{"learner_id": "L1", "mastery": {}, "uncertainty": {}}]}
    assert load_c2_learner(data, "L1")["learner_id"] == "L1"


def test_c3_contract_validator_accepts_fixture() -> None:
    validate_c3_path({
        "learner_id": "L1", "target": "heap", "verified": True,
        "path": [{"kind": "learn", "id": "heap"}],
    })


def test_c1_csv_adapter_marks_relations_as_candidates(tmp_path: Path) -> None:
    concepts = tmp_path / "concepts.csv"
    relations = tmp_path / "relations.csv"
    concepts.write_text("concept\nheap\nbinary tree\n", encoding="utf-8")
    relations.write_text(
        "relation_type,concept_a,concept_b,source_text\n"
        "prerequisite-of,binary tree,heap,example\n",
        encoding="utf-8",
    )
    graph = load_c1_csv_graph(concepts, relations)
    assert graph["concepts"]["heap"]["prerequisites"] == ["binary_tree"]
    assert "unverified candidates" in graph["_note"]

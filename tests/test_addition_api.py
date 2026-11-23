from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from c4.server import create_server
from c4.service import Workbench
from tests.stubs import StubGenerator


@pytest.fixture(scope="module")
def bench() -> Workbench:
    return Workbench(generator=StubGenerator())


@pytest.fixture(scope="module")
def base_url(bench):
    server = create_server("127.0.0.1", 0, bench)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def post(url: str, payload: dict):
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def test_teachback_prompt_lists_lecture_concepts_and_examples(bench: Workbench) -> None:
    result = bench.teachback_prompt({"target": "heap"})
    assert result["concepts"] == ["heap", "binary_tree", "arrays"] and result["test_items"] > 5
    assert set(result["examples"]) >= {"complete", "wrong", "empty"}


def test_teachback_scores_good_above_wrong_and_empty(bench: Workbench) -> None:
    ex = bench.teachback_prompt({"target": "heap"})["examples"]
    score = lambda text: bench.teachback({"target": "heap", "explanation": text})["novice_test"]["overall"]["score"]
    assert score(ex["complete"]) > score(ex["wrong"]) >= score(ex["empty"]) == 0.0


def test_teachback_rejects_bad_input(bench: Workbench) -> None:
    with pytest.raises(ValueError):
        bench.teachback({"target": "heap", "explanation": 5})
    with pytest.raises(ValueError):
        bench.teachback({"target": "heap", "explanation": "x", "novice": "gpt"})


def test_audit_demo_lists_planted_truth_and_validates_input(bench: Workbench) -> None:
    result = bench.audit_demo({"students": 200, "seed": 1})
    truths = {row["truth"] for row in result["edges"]}
    assert {"true edge", "reversed", "spurious"} <= truths and result["planted"]["reversed"] >= 1
    for bad in ({"students": 5}, {"seed": -1}, {"fraction": 0.9}):
        with pytest.raises(ValueError):
            bench.audit_demo(bad)


def test_help_flow_over_http(base_url) -> None:
    status, start = post(f"{base_url}/api/help", {"target": "heap", "stage": "start"})
    assert status == 200 and start["next"] == "attempt" and start["mastery_evidence"] is None
    status, refused = post(f"{base_url}/api/help", {"target": "heap", "stage": "explain"})
    assert status == 200 and refused["refused"]
    status, bad = post(f"{base_url}/api/help", {"target": "nope", "stage": "start"})
    assert status == 400


def test_teachback_and_audit_over_http(base_url) -> None:
    status, body = post(f"{base_url}/api/teachback", {"target": "heap", "explanation": "A heap is a complete binary tree."})
    assert status == 200 and body["evidence"] and body["use"].startswith("formative")
    status, body = post(f"{base_url}/api/audit", {"students": 120})
    assert status == 200 and body["counts"]
    status, body = post(f"{base_url}/api/audit", {"students": "many"})
    assert status == 400


def test_results_include_the_new_artefacts(bench: Workbench) -> None:
    results = bench.results()
    assert {"teachback", "audit", "planner"} <= set(results)

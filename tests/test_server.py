from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from c4.server import create_server
from c4.service import Workbench


@pytest.fixture(scope="module")
def base_url():
    server = create_server("127.0.0.1", 0, Workbench())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def call(url: str, payload=None, raw: bytes | None = None):
    data = raw if raw is not None else (None if payload is None else json.dumps(payload).encode())
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()


def test_health_reports_status_and_ollama_flag(base_url) -> None:
    status, _, body = call(f"{base_url}/api/health")
    assert status == 200 and json.loads(body)["status"] == "ok"
    assert "online" in json.loads(body)["ollama"]


def test_meta_and_results_endpoints(base_url) -> None:
    assert len(json.loads(call(f"{base_url}/api/meta")[2])["targets"]) == 7
    assert json.loads(call(f"{base_url}/api/results")[2])["stress"]["cases"] == 28


def test_verify_round_trip(base_url) -> None:
    status, headers, body = call(f"{base_url}/api/verify", {
        "target": "heap", "explanation": "A heap is always fully sorted."})
    report = json.loads(body)
    assert status == 200 and headers["Content-Type"].startswith("application/json")
    assert report["initial_claims"][0]["factual_status"] == "CONTRADICTED"
    assert report["claims"][0]["accepted"] is True


@pytest.mark.parametrize("payload,raw,expected", [
    ({"target": "nope", "explanation": "x"}, None, 400),
    (None, b"not json", 400),
    (None, b"[1, 2]", 400),
    (None, b"", 400),
])
def test_bad_requests_return_400_with_error_message(base_url, payload, raw, expected) -> None:
    status, _, body = call(f"{base_url}/api/verify", payload, raw)
    assert status == expected and "error" in json.loads(body)


def test_oversized_body_is_rejected(base_url) -> None:
    status, _, _ = call(f"{base_url}/api/verify", raw=b"{" + b" " * (300 * 1024) + b"}")
    assert status == 413


def test_template_generation_endpoint(base_url) -> None:
    status, _, body = call(f"{base_url}/api/generate", {"target": "arrays", "source": "template"})
    assert status == 200 and "Arrays" in json.loads(body)["explanation"]


def test_unknown_routes_and_path_traversal_are_404(base_url) -> None:
    assert call(f"{base_url}/api/nothing")[0] == 404
    assert call(f"{base_url}/api/nothing", {"a": 1})[0] == 404
    assert call(f"{base_url}/../pipeline.py")[0] == 404
    assert call(f"{base_url}/%2e%2e/pipeline.py")[0] == 404


def test_static_index_is_served(base_url) -> None:
    status, headers, body = call(f"{base_url}/")
    assert status == 200 and headers["Content-Type"].startswith("text/html") and b"C4" in body


def test_self_hosted_font_is_served_with_a_font_type(base_url) -> None:
    status, headers, body = call(f"{base_url}/fonts/JosefinSans.ttf")
    assert status == 200 and headers["Content-Type"] == "font/ttf" and len(body) > 50_000
    assert call(f"{base_url}/fonts/OFL.txt")[0] == 200


def test_explain_endpoint_runs_the_whole_pipeline(base_url) -> None:
    status, _, body = call(f"{base_url}/api/explain", {"target": "arrays", "source": "template"})
    report = json.loads(body)
    assert status == 200 and report["generator"] == "template" and report["schema_version"] == "c4-report/1.2"

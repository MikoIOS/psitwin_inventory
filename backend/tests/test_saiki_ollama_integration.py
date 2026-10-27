"""Opt-in real local Ollama, real HTTP/JWT, exclusively synthetic database."""
import asyncio
import json
import os
from pathlib import Path
import time

import pytest

from app.controllers import saiki_controller
from tests.test_saiki_http import http_app, post


@pytest.mark.skipif(os.environ.get("SAIKI_REAL_OLLAMA_TEST") != "1", reason="Real Ollama opt-in required")
def test_local_ollama_is_not_called_for_simple_location(http_app, monkeypatch):
    app, _ = http_app
    inference_times = []
    tool_times = []
    real_call = saiki_controller.service._call_ollama_chat
    real_execute = saiki_controller.service.tools.execute
    def measured_call(*args, **kwargs):
        started = time.perf_counter()
        try:
            return real_call(*args, **kwargs)
        finally:
            inference_times.append((time.perf_counter() - started) * 1000)
    async def measured_execute(name, args, user=None):
        started = time.perf_counter()
        try:
            return await real_execute(name, args, user)
        finally:
            tool_times.append({"name": name, "duration_ms": (time.perf_counter() - started) * 1000})
    monkeypatch.setattr(saiki_controller.service, "_call_ollama_chat", measured_call)
    monkeypatch.setattr(saiki_controller.service.tools, "execute", measured_execute)
    started = time.perf_counter()
    response = asyncio.run(post(app, "¿Dónde está el arroz?"))
    measurement = {"kind": "real_fastapi_jwt_ollama_available_but_bypassed_synthetic_database", "status": response.status_code, "total_ms": (time.perf_counter() - started) * 1000, "inference_times_ms": inference_times, "tools": tool_times, "response": response.json()}
    output = Path("venv/saiki-tests-py312/real-ollama-measurement.json")
    output.write_text(json.dumps(measurement, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Real Ollama: HTTP {response.status_code}; total {measurement['total_ms']:.3f} ms; calls {len(inference_times)}")
    assert response.status_code == 200, response.text
    assert inference_times == []
    payload = response.json()
    assert payload["sources"], "Operational facts require a tool source"
    assert payload["answer"].strip()
    assert "B-product" not in json.dumps(payload, ensure_ascii=False)
    assert "B-inventory" not in json.dumps(payload, ensure_ascii=False)

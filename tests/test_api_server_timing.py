"""Tests for the Server-Timing response header."""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

_TIMING_RE = re.compile(r"^app;dur=\d+(?:\.\d+)?$")


def test_health_reports_server_timing():
    response = client.get("/health")
    assert response.status_code == 200
    timing = response.headers.get("server-timing")
    assert timing is not None
    assert _TIMING_RE.match(timing)


def test_server_timing_present_on_not_found():
    response = client.get("/definitely-not-a-route")
    assert response.status_code == 404
    assert _TIMING_RE.match(response.headers["server-timing"])


def test_server_timing_duration_is_non_negative():
    for _ in range(3):
        response = client.get("/health")
        duration = float(response.headers["server-timing"].split("dur=")[1])
        assert duration >= 0.0

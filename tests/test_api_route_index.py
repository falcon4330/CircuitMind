"""Tests for the GET /api/routes discovery endpoint."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_route_index_lists_core_endpoints():
    response = client.get("/api/routes")
    assert response.status_code == 200

    data = response.json()
    paths = {entry["path"] for entry in data["routes"]}
    assert {"/generate", "/explain", "/diagnose", "/export", "/hint"} <= paths
    assert data["count"] == len(data["routes"])


def test_route_index_skips_documentation_paths():
    data = client.get("/api/routes").json()
    for entry in data["routes"]:
        assert not entry["path"].startswith(("/docs", "/redoc", "/openapi"))


def test_route_index_entries_carry_upper_case_methods():
    data = client.get("/api/routes").json()
    for entry in data["routes"]:
        assert entry["methods"]
        assert all(method == method.upper() for method in entry["methods"])


def test_route_index_is_sorted_by_path():
    data = client.get("/api/routes").json()
    paths = [entry["path"] for entry in data["routes"]]
    assert paths == sorted(paths)

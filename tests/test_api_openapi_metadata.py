"""Tests for the OpenAPI metadata published by the API app."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_openapi_info_has_contact():
    info = app.openapi()["info"]
    assert info["contact"]["name"] == "QuantumLogicsLabs"
    assert info["contact"]["url"].startswith("https://github.com/")


def test_openapi_info_has_license():
    info = app.openapi()["info"]
    assert "PPSLA" in info["license"]["name"]


def test_openapi_tags_are_documented():
    tags = {tag["name"]: tag for tag in app.openapi_tags}
    assert {"health", "core"} <= set(tags)
    for tag in tags.values():
        assert tag.get("description")


def test_openapi_paths_reference_declared_tags():
    spec = app.openapi()
    declared = {tag["name"] for tag in spec["tags"]}
    for path_item in spec["paths"].values():
        for operation in path_item.values():
            for tag in operation.get("tags", []):
                assert tag in declared


def test_openapi_document_served_over_http():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "CircuitMind API"

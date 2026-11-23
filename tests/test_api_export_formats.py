"""Tests for GET /export/formats."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from api.app import app
from export.export_module import VALID_FORMATS

client = TestClient(app)


def test_export_formats_lists_every_supported_format():
    response = client.get("/export/formats")
    assert response.status_code == 200

    data = response.json()
    names = [item["name"] for item in data["formats"]]
    assert names == sorted(VALID_FORMATS)
    assert data["count"] == len(VALID_FORMATS)


def test_export_formats_entries_have_descriptions():
    data = client.get("/export/formats").json()
    for item in data["formats"]:
        assert item["name"]
        assert item["description"]


def test_export_formats_includes_known_formats():
    names = {item["name"] for item in client.get("/export/formats").json()["formats"]}
    assert {"spice", "svg", "gate_json"} <= names

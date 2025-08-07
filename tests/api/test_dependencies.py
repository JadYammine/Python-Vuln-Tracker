import pytest
from fastapi.testclient import TestClient

from src.main import app

def test_list_dependencies(monkeypatch):
    # Patch scan_project to avoid background scan
    async def fake_scan_project(project_id):
        pass
    monkeypatch.setattr("src.api.projects.scan_project", fake_scan_project)

    with TestClient(app) as client:
        # Create a project with a dependency
        files = {"requirements": ("requirements.txt", b"flask==1.1.2\n")}
        data = {"name": "DepProj", "description": "desc"}
        client.post("/api/projects/", data=data, files=files)
        # List dependencies
        resp = client.get("/api/dependencies/")
        assert resp.status_code == 200
        deps = resp.json()
        assert any(d["name"] == "flask" for d in deps)

def test_get_dependency_not_found():
    with TestClient(app) as client:
        resp = client.get("/api/dependencies/nonexistent-id/nonexistent-version")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Dependency not found or not scanned yet"

import pytest
from fastapi.testclient import TestClient

from src.main import app

def test_create_project(monkeypatch):
    # Patch scan_project to avoid background scan
    async def fake_scan_project(project_id):
        pass
    monkeypatch.setattr("src.api.projects.scan_project", fake_scan_project)

    with TestClient(app) as client:
        files = {"requirements": ("requirements.txt", b"requests==2.25.1\n")}
        data = {"name": "TestProj", "description": "desc"}
        resp = client.post("/api/projects/", data=data, files=files)
        assert resp.status_code == 202
        project = resp.json()
        assert project["name"] == "TestProj"
        assert project["description"] == "desc"
        assert "id" in project
        assert project["status"] in ("PENDING", "SCANNING", "DONE", "ERROR")

def test_list_projects(monkeypatch):
    async def fake_scan_project(project_id):
        pass
    monkeypatch.setattr("src.api.projects.scan_project", fake_scan_project)

    with TestClient(app) as client:
        # Create a project
        files = {"requirements": ("requirements.txt", b"flask==1.1.2\n")}
        data = {"name": "DepProj", "description": "desc"}
        client.post("/api/projects/", data=data, files=files)
        # List projects
        resp = client.get("/api/projects/")
        assert resp.status_code == 200
        projects = resp.json()
        assert any(p["name"] == "DepProj" for p in projects)

def test_get_project_not_found():
    with TestClient(app) as client:
        resp = client.get("/api/projects/nonexistent-id")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Project not found"

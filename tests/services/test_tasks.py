import pytest
import asyncio
import orjson

from src.domain.project import Project, ScanState
from src.domain.dependency import Dependency, Vulnerability
from src.infra import storage
from src.services import tasks

@pytest.mark.asyncio
async def test_scan_project_marks_done_and_populates_vulns(monkeypatch):
    dep = Dependency(name="requests", version="2.25.1")
    project = Project(name="proj", dependencies=[dep])
    storage.projects.add(project)
    project_id = str(project.id)

    fake_ids_map = {"requests==2.25.1": ["OSV-1"]}
    fake_vuln = Vulnerability(id="OSV-1", summary="Test vuln", severity="HIGH", references=["url"])

    async def fake_batch_query(deps):
        return fake_ids_map
    async def fake_vuln_detail(vuln_id):
        return fake_vuln

    monkeypatch.setattr(tasks.osv_client, "batch_query", fake_batch_query)
    monkeypatch.setattr(tasks.osv_client, "vuln_detail", fake_vuln_detail)

    await tasks.scan_project(project_id)
    proj = storage.projects.get(project_id)
    assert proj.status == ScanState.DONE
    assert proj.dependencies[0].vulnerabilities
    assert proj.dependencies[0].vulnerabilities[0].id == "OSV-1"

@pytest.mark.asyncio
async def test_scan_project_handles_missing_project():
    await tasks.scan_project("nonexistent-id")

@pytest.mark.asyncio
async def test_scan_project_error_sets_status(monkeypatch):
    dep = Dependency(name="flask", version="1.1.2")
    project = Project(name="proj2", dependencies=[dep])
    storage.projects.add(project)
    project_id = str(project.id)

    async def fake_batch_query(deps):
        raise Exception("fail")

    monkeypatch.setattr(tasks.osv_client, "batch_query", fake_batch_query)
    await tasks.scan_project(project_id)
    proj = storage.projects.get(project_id)
    assert proj.status == ScanState.ERROR

@pytest.mark.asyncio
async def test_scan_project_concurrent(monkeypatch):
    # Arrange: create multiple projects
    deps = [
        Dependency(name="requests", version="2.25.1"),
        Dependency(name="flask", version="1.1.2")
    ]
    projects = [
        Project(name=f"proj{i}", dependencies=[dep])
        for i, dep in enumerate(deps)
    ]
    for proj in projects:
        storage.projects.add(proj)
    ids = [str(proj.id) for proj in projects]

    # Patch OSVClient methods to simulate different vulns
    fake_ids_maps = [
        {"requests==2.25.1": ["OSV-1"]},
        {"flask==1.1.2": ["OSV-2"]}
    ]
    fake_vulns = [
        Vulnerability(id="OSV-1", summary="Vuln1", severity="HIGH", references=["url1"]),
        Vulnerability(id="OSV-2", summary="Vuln2", severity="LOW", references=["url2"])
    ]

    async def fake_batch_query(deps):
        if ("requests", "2.25.1") in deps:
            return fake_ids_maps[0]
        else:
            return fake_ids_maps[1]

    async def fake_vuln_detail(vuln_id):
        if vuln_id == "OSV-1":
            return fake_vulns[0]
        else:
            return fake_vulns[1]

    monkeypatch.setattr(tasks.osv_client, "batch_query", fake_batch_query)
    monkeypatch.setattr(tasks.osv_client, "vuln_detail", fake_vuln_detail)

    # Act: scan all projects concurrently
    await asyncio.gather(*(tasks.scan_project(pid) for pid in ids))

    # Assert: all projects are marked done and have correct vulns
    for i, pid in enumerate(ids):
        proj = storage.projects.get(pid)
        assert proj.status == ScanState.DONE
        assert proj.dependencies[0].vulnerabilities
        assert proj.dependencies[0].vulnerabilities[0].id == fake_vulns[i].id

@pytest.mark.asyncio
async def test_scan_project_status_transitions(monkeypatch):
    dep = Dependency(name="requests", version="2.25.1")
    project = Project(name="proj-status", dependencies=[dep])
    storage.projects.add(project)
    project_id = str(project.id)

    fake_ids_map = {"requests==2.25.1": ["OSV-1"]}
    fake_vuln = Vulnerability(id="OSV-1", summary="Test vuln", severity="HIGH", references=["url"])

    async def fake_batch_query(deps):
        # Check status is SCANNING during call
        proj = storage.projects.get(project_id)
        assert proj.status == ScanState.SCANNING
        return fake_ids_map
    async def fake_vuln_detail(vuln_id):
        return fake_vuln

    monkeypatch.setattr(tasks.osv_client, "batch_query", fake_batch_query)
    monkeypatch.setattr(tasks.osv_client, "vuln_detail", fake_vuln_detail)

    await tasks.scan_project(project_id)
    proj = storage.projects.get(project_id)
    assert proj.status == ScanState.DONE

@pytest.mark.asyncio
async def test_scan_project_cache_hit(monkeypatch):
    dep = Dependency(name="requests", version="2.25.1")
    project = Project(name="proj-cache", dependencies=[dep])
    storage.projects.add(project)
    project_id = str(project.id)

    post_calls = {"count": 0}
    get_calls = {"count": 0}

    class FakePostResp:
        def raise_for_status(self): pass
        @property
        def content(self):
            return orjson.dumps({"results": [{"vulns": [{"id": "OSV-1"}]}]})

    class FakeGetResp:
        def raise_for_status(self): pass
        @property
        def content(self):
            return orjson.dumps({
                "id": "OSV-1",
                "summary": "Test vuln",
                "severity": [{"score": "HIGH"}],
                "references": [{"url": "url"}]
            })

    async def fake_post(self, url, content, headers):
        post_calls["count"] += 1
        return FakePostResp()

    async def fake_get(self, url):
        get_calls["count"] += 1
        return FakeGetResp()

    monkeypatch.setattr(tasks.osv_client.client, "post", fake_post.__get__(tasks.osv_client.client))
    monkeypatch.setattr(tasks.osv_client.client, "get", fake_get.__get__(tasks.osv_client.client))

    # First scan (should call both)
    await tasks.scan_project(project_id)
    # Second scan (should hit cache, not call again)
    await tasks.scan_project(project_id)

    assert post_calls["count"] == 1
    assert get_calls["count"] == 1
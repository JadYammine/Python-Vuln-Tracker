import pytest
import httpx
import orjson

from src.services.osv_client import OSVClient
from src.domain.dependency import Vulnerability

@pytest.mark.asyncio
async def test_batch_query_success(monkeypatch):
    # Arrange
    deps = [("requests", "2.25.1"), ("flask", "1.1.2")]
    fake_response = {
        "results": [
            {"vulns": [{"id": "OSV-2021-1"}]},
            {"vulns": []}
        ]
    }
    async def fake_post(url, content, headers):
        class Resp:
            def raise_for_status(self):
                pass
            @property
            def content(self):
                return orjson.dumps(fake_response)
        return Resp()
    client = OSVClient()
    monkeypatch.setattr(client.client, "post", fake_post)

    # Act
    result = await client.batch_query(deps)

    # Assert
    assert result == {
        "requests==2.25.1": ["OSV-2021-1"],
        "flask==1.1.2": []
    }

@pytest.mark.asyncio
async def test_vuln_detail_success(monkeypatch):
    vuln_id = "OSV-2021-1"
    fake_data = {
        "id": vuln_id,
        "summary": "A test vuln",
        "severity": [{"score": "HIGH"}],
        "references": [{"url": "https://osv.dev/vuln/OSV-2021-1"}]
    }
    async def fake_get(url):
        class Resp:
            def raise_for_status(self):
                pass
            @property
            def content(self):
                return orjson.dumps(fake_data)
        return Resp()
    client = OSVClient()
    monkeypatch.setattr(client.client, "get", fake_get)
    vuln = await client.vuln_detail(vuln_id)
    assert isinstance(vuln, Vulnerability)
    assert vuln.id == vuln_id
    assert vuln.summary == "A test vuln"
    assert vuln.severity == "HIGH"
    assert "https://osv.dev/vuln/OSV-2021-1" in vuln.references

@pytest.mark.asyncio
async def test_batch_query_http_error(monkeypatch):
    deps = [("requests", "2.25.1")]
    class FakeResp:
        def raise_for_status(self):
            raise httpx.HTTPStatusError("error", request=None, response=None)
        @property
        def content(self):
            return b"{}"
    async def fake_post(url, content, headers):
        return FakeResp()
    client = OSVClient()
    monkeypatch.setattr(client.client, "post", fake_post)
    with pytest.raises(httpx.HTTPStatusError):
        await client.batch_query(deps)

@pytest.mark.asyncio
async def test_vuln_detail_http_error(monkeypatch):
    vuln_id = "OSV-2021-1"
    class FakeResp:
        def raise_for_status(self):
            raise httpx.HTTPStatusError("error", request=None, response=None)
        @property
        def content(self):
            return b"{}"
    async def fake_get(url):
        return FakeResp()
    client = OSVClient()
    monkeypatch.setattr(client.client, "get", fake_get)
    with pytest.raises(httpx.HTTPStatusError):
        await client.vuln_detail(vuln_id)

@pytest.mark.asyncio
async def test_counters_increment(monkeypatch):
    deps = [("requests", "2.25.1")]
    fake_response = {"results": [{"vulns": []}]}
    async def fake_post(url, content, headers):
        class Resp:
            def raise_for_status(self):
                pass
            @property
            def content(self):
                return orjson.dumps(fake_response)
        return Resp()
    async def fake_get(url):
        class Resp:
            def raise_for_status(self):
                pass
            @property
            def content(self):
                return orjson.dumps({"id": "OSV-1", "references": []})
        return Resp()
    client = OSVClient()
    monkeypatch.setattr(client.client, "post", fake_post)
    monkeypatch.setattr(client.client, "get", fake_get)
    await client.batch_query(deps)
    await client.vuln_detail("OSV-1")
    counters = client.get_counters()
    assert counters["batch_queries"] == 1
    assert counters["detail_lookups"] == 1

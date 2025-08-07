import httpx
from typing import List, Tuple

from ..utils.cache import ttl_cache
from ..domain.dependency import Vulnerability

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL  = "https://api.osv.dev/v1/vulns"

class OSVClient:
    def __init__(self, timeout: int = 10):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.counter_batch = 0
        self.counter_detail = 0

    def get_counters(self):
        """
        Returns the current counters for batch queries and detail lookups.
        Useful for debugging and monitoring.
        """
        return {
            "batch_queries": self.counter_batch,
            "detail_lookups": self.counter_detail,
        }

    async def aclose(self):
        await self.client.aclose()

    @ttl_cache(seconds=12 * 3600)
    async def batch_query(self, deps: List[Tuple[str, str]]) -> dict[str, list[str]]:
        """
        deps: list of (name, version)
        returns: {"name==version": [vuln_id, ...], ...}
        """
        self.counter_batch += 1
        payload = {
            "queries": [
                {"package": {"name": name, "ecosystem": "PyPI"}, "version": ver}
                for name, ver in deps
            ]
        }
        r = await self.client.post(OSV_BATCH_URL, json=payload)
        r.raise_for_status()
        results = r.json()["results"]           # guaranteed same order as input

        return {
            f"{n}=={v}": [vuln["id"] for vuln in res.get("vulns", [])]
            for (n, v), res in zip(deps, results)
        }



    @ttl_cache(seconds=12 * 3600)
    async def vuln_detail(self, vuln_id: str) -> Vulnerability:
        """
        Fetches detailed information about a specific vulnerability by its ID.
        Returns a Vulnerability object.
        """
        self.counter_detail += 1
        res = await self.client.get(f"{OSV_VULN_URL}/{vuln_id}")
        res.raise_for_status()
        data = res.json()
        return Vulnerability(
            id=data["id"],
            summary=data.get("summary"),
            severity=data.get("severity", [{}])[0].get("score") if data.get("severity") else None,
            references=[r["url"] for r in data.get("references", [])],
        )

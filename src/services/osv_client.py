import httpx
import asyncio
import orjson
from typing import List, Tuple
from contextlib import asynccontextmanager

from ..utils.cache import ttl_cache
from ..domain.dependency import Vulnerability

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL  = "https://api.osv.dev/v1/vulns"

class OSVClient:
    def __init__(self, timeout: int = 30, max_connections: int = 20, rate_limit: int = 100):
        self.timeout = timeout
        self.max_connections = max_connections
        self.rate_limit = rate_limit
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.client = None
        self.counter_batch = 0
        self.counter_detail = 0
        self._setup_client()

    def _setup_client(self):
        """Initialize HTTP client with connection pooling and HTTP/2"""
        limits = httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=10,
            keepalive_expiry=60.0  # Longer keepalive for HTTP/2
        )
        
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=limits,
            http2=True,  # Enable HTTP/2 for better multiplexing
            headers={
                "User-Agent": "Python-Vuln-Tracker/1.0",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, br"  # Support brotli compression
            }
        )

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
        if self.client:
            await self.client.aclose()

    @asynccontextmanager
    async def _rate_limited(self):
        """Rate limiting context manager"""
        async with self.semaphore:
            yield

    @ttl_cache(seconds=12 * 3600, max_size=500)
    async def batch_query(self, deps: List[Tuple[str, str]]) -> dict[str, list[str]]:
        """
        deps: list of (name, version)
        returns: {"name==version": [vuln_id, ...], ...}
        """
        async with self._rate_limited():
            self.counter_batch += 1
            
            # Split large batches to avoid timeouts
            batch_size = 50
            results = {}
            
            for i in range(0, len(deps), batch_size):
                batch = deps[i:i + batch_size]
                payload = {
                    "queries": [
                        {"package": {"name": name, "ecosystem": "PyPI"}, "version": ver}
                        for name, ver in batch
                    ]
                }
                
                try:
                    # Use orjson for faster JSON serialization
                    json_payload = orjson.dumps(payload)
                    r = await self.client.post(
                        OSV_BATCH_URL, 
                        content=json_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    r.raise_for_status()
                    # Use orjson for faster JSON deserialization
                    batch_results = orjson.loads(r.content)["results"]
                    
                    batch_dict = {
                        f"{n}=={v}": [vuln["id"] for vuln in res.get("vulns", [])]
                        for (n, v), res in zip(batch, batch_results)
                    }
                    results.update(batch_dict)
                    
                except httpx.HTTPStatusError as e:
                    status_code = getattr(getattr(e, "response", None), "status_code", None)
                    if status_code == 429:  # Rate limited
                        await asyncio.sleep(1)  # Wait and retry
                        continue
                    raise
                except Exception as e:
                    # Log error but continue with other batches
                    print(f"Batch query error: {e}")
                    continue
            
            return results

    @ttl_cache(seconds=12 * 3600, max_size=1000)
    async def vuln_detail(self, vuln_id: str) -> Vulnerability:
        """
        Fetches detailed information about a specific vulnerability by its ID.
        Returns a Vulnerability object.
        """
        async with self._rate_limited():
            self.counter_detail += 1
            
            try:
                res = await self.client.get(f"{OSV_VULN_URL}/{vuln_id}")
                res.raise_for_status()
                # Use orjson for faster JSON deserialization
                data = orjson.loads(res.content)
                
                return Vulnerability(
                    id=data["id"],
                    summary=data.get("summary"),
                    severity=data.get("severity", [{}])[0].get("score") if data.get("severity") else None,
                    references=[r["url"] for r in data.get("references", [])],
                )
            except httpx.HTTPStatusError as e:
                status_code = getattr(getattr(e, "response", None), "status_code", None)
                if status_code == 429:  # Rate limited
                    await asyncio.sleep(0.5)
                    return await self.vuln_detail(vuln_id)  # Retry
                raise
            except Exception as e:
                print(f"Vulnerability detail error for {vuln_id}: {e}")
                # Return a minimal vulnerability object
                return Vulnerability(
                    id=vuln_id,
                    summary="Error fetching details",
                    severity=None,
                    references=[]
                )

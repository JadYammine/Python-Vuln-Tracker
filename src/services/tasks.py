import asyncio
import logging
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor
import time

from ..infra.storage import projects, dep_index
from ..domain.project import ScanState
from ..domain.dependency import Vulnerability
from .osv_client import OSVClient

logger = logging.getLogger(__name__)

# Global thread pool for CPU-bound tasks
thread_pool = ThreadPoolExecutor(max_workers=4)

# Semaphore to limit concurrent scans
scan_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent scans

osv_client = OSVClient()

async def scan_project(project_id: str):
    """
    Enhanced project scanning with better concurrency control and error handling.
    • Change status ➜ SCANNING
    • Perform batch OSV lookup
    • Populate Dependency.vulnerabilities
    • Update dep_index
    """
    async with scan_semaphore:  # Limit concurrent scans
        start_time = time.perf_counter()
        
        project = projects.get(project_id)
        if not project:
            logger.error("Project %s disappeared before scanning", project_id)
            return

        project.status = ScanState.SCANNING
        logger.info(f"Starting scan for project {project_id} with {len(project.dependencies)} dependencies")

        deps_tuples: List[Tuple[str, str]] = [
            (d.name, d.version) for d in project.dependencies
        ]

        try:
            # Batch query with timeout
            ids_map = await asyncio.wait_for(
                osv_client.batch_query(deps_tuples),
                timeout=60  # 60 second timeout
            )
            
            # Fetch unique vuln-IDs concurrently with chunking
            uniq_ids = {vid for vids in ids_map.values() for vid in vids}
            logger.info(f"Found {len(uniq_ids)} unique vulnerabilities to fetch")
            
            # Process vulnerability details in chunks to avoid overwhelming the API
            chunk_size = 20
            detail_map = {}
            
            for i in range(0, len(uniq_ids), chunk_size):
                chunk = list(uniq_ids)[i:i + chunk_size]
                tasks = [osv_client.vuln_detail(vid) for vid in chunk]
                
                try:
                    chunk_results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=30
                    )
                    
                    # Handle any exceptions in the chunk
                    for vid, result in zip(chunk, chunk_results):
                        if isinstance(result, Exception):
                            logger.warning(f"Failed to fetch vuln {vid}: {result}")
                            # Create a fallback vulnerability
                            detail_map[vid] = Vulnerability(
                                id=vid,
                                summary="Error fetching details",
                                severity=None,
                                references=[]
                            )
                        else:
                            detail_map[vid] = result
                    
                    # Small delay between chunks to be respectful to the API
                    if i + chunk_size < len(uniq_ids):
                        await asyncio.sleep(0.1)
                        
                except asyncio.TimeoutError:
                    logger.error(f"Timeout fetching vulnerability details chunk {i//chunk_size}")
                    continue
            
            # Attach vulnerability objects to dependencies
            for dep in project.dependencies:
                vids = ids_map.get(f"{dep.name}=={dep.version}", [])
                dep.vulnerabilities = [detail_map.get(vid) for vid in vids if vid in detail_map]

                # Add to global index once populated
                dep_index.add(dep)

            project.status = ScanState.DONE
            scan_time = time.perf_counter() - start_time
            logger.info(f"Scan completed for project {project_id} in {scan_time:.2f}s")

        except asyncio.TimeoutError:
            logger.error(f"Scan timeout for project {project_id}")
            project.status = ScanState.ERROR
        except Exception as exc:
            logger.exception(f"Scan failed for project {project_id}: {exc}")
            project.status = ScanState.ERROR

async def get_scan_stats():
    """Get statistics about current scanning operations"""
    return {
        "concurrent_scans": scan_semaphore._value,
        "osv_client_stats": osv_client.get_counters(),
        "cache_stats": {
            "batch_query": osv_client.batch_query.cache_stats(),
            "vuln_detail": osv_client.vuln_detail.cache_stats()
        }
    }
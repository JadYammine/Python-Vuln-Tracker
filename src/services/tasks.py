import asyncio, logging
from typing import List, Tuple

from ..infra.storage import projects, dep_index
from ..domain.project import ScanState
from .osv_client import OSVClient

logger = logging.getLogger(__name__)


osv_client = OSVClient()

async def scan_project(project_id: str):
    """
    • Change status ➜ SCANNING
    • Perform batch OSV lookup
    • Populate Dependency.vulnerabilities
    • Update dep_index
    """
    project = projects.get(project_id)
    if not project:
        logger.error("Project %s disappeared before scanning", project_id)
        return

    project.status = ScanState.SCANNING

    deps_tuples: List[Tuple[str, str]] = [
        (d.name, d.version) for d in project.dependencies
    ]

    try:
        ids_map = await osv_client.batch_query(deps_tuples)               # cache #1
        # Fetch unique vuln-IDs concurrently (cache #2)
        uniq_ids = {vid for vids in ids_map.values() for vid in vids}
        
        tasks = [osv_client.vuln_detail(vid) for vid in uniq_ids]         # cache #2
        results = await asyncio.gather(*tasks)
        detail_map = dict(zip(uniq_ids, results))
        
        # attach vuln objects
        for dep in project.dependencies:
            vids = ids_map.get(f"{dep.name}=={dep.version}", [])
            dep.vulnerabilities = [detail_map[vid] for vid in vids]

            # add to global index once populated
            dep_index.add(dep)

        project.status = ScanState.DONE

    except Exception as exc:            # handle any errors during the scan
        logger.exception("Scan failed: %s", exc)
        project.status = ScanState.ERROR
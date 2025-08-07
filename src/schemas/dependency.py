from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from ..domain.dependency import Dependency, Vulnerability

class DependencySummary(BaseModel):
    """Thin response model for GET /dependencies (list endpoint)."""
    name: str
    version: str
    vulnerable: bool          # TRUE if any CVE hits
    vuln_count: Optional[int] = None

    @classmethod
    def from_domain(cls, dep: Dependency) -> "DependencySummary":
        return cls(
            name=dep.name,
            version=dep.version,
            vulnerable=dep.vulnerable,
            vuln_count=len(dep.vulnerabilities) if dep.vulnerabilities else 0,
        )


class DependencyDetail(BaseModel):
    """Detailed response model for GET /dependencies/{name}/{version}."""
    name: str
    version: str
    vulnerable: bool
    usage_count: int           # how many projects include it
    project_ids: List[UUID]    # those project UUIDs
    vulnerabilities: List[Vulnerability]

    @classmethod
    def from_domain(
        cls, dep: Dependency, project_ids: List[UUID]
    ) -> "DependencyDetail":
        return cls(
            name=dep.name,
            version=dep.version,
            vulnerable=dep.vulnerable,
            usage_count=len(project_ids) if project_ids else 0,
            project_ids=project_ids,
            vulnerabilities=dep.vulnerabilities,
        )
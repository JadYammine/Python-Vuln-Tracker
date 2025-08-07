from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from ..domain.project import Project, ScanState
from .dependency import DependencySummary

class ProjectCreateResponse(BaseModel):
    """Thin response model for POST /projects."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: ScanState

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectCreateResponse":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
        )

class ProjectSummary(BaseModel):
    """Thin response model for GET /projects (list endpoint)."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: ScanState
    vulnerable: bool           # ← computed from the domain entity

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectSummary":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            vulnerable=project.vulnerable,
        )
    
class ProjectDetail(BaseModel):
    """Detailed response model for GET /projects/{project_id}."""
    id: UUID
    name: str
    description: Optional[str] = None
    status: ScanState
    vulnerable: bool           # ← computed from the domain entity
    dependencies: List[DependencySummary]  # List of Dependency objects

    @classmethod
    def from_domain(cls, project: Project) -> "ProjectDetail":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            status=project.status,
            vulnerable=project.vulnerable,
            dependencies=[DependencySummary.from_domain(dep) for dep in project.dependencies],
        )
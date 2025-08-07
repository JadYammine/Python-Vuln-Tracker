from __future__ import annotations
from uuid import UUID, uuid4
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field
from .dependency import Dependency


class ScanState(str, Enum):
    PENDING = "PENDING"
    SCANNING = "SCANNING"
    DONE = "DONE"
    ERROR = "ERROR"


class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    status: ScanState = ScanState.PENDING
    dependencies: List[Dependency] = Field(default_factory=list)

    @computed_field
    @property
    def vulnerable(self) -> bool:
        return any(dep.vulnerable for dep in self.dependencies)

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field

class Vulnerability(BaseModel):
    id: str
    summary: Optional[str] = None
    severity: Optional[str] = None
    references: list[str] = []


class Dependency(BaseModel):
    name: str
    version: str
    vulnerabilities: List[Vulnerability] = Field(default_factory=list)

    @computed_field
    @property
    def vulnerable(self) -> bool:
        return bool(self.vulnerabilities)
from fastapi import APIRouter, HTTPException

from ..schemas.dependency import DependencySummary, DependencyDetail
from ..infra.storage import dep_index, dep_usage

router = APIRouter(prefix="/dependencies")


@router.get("/", response_model=list[DependencySummary])
async def list_dependencies():
    """Return one summary per unique name==version pair."""
    return [
        DependencySummary.from_domain(deps[0])
        for deps in dep_index.all()
        if deps
    ]


@router.get("/{name}/{version}", response_model=DependencyDetail)
async def dependency_detail(name: str, version: str):
    key = f"{name.lower()}=={version}"
    deps = dep_index.get(key)
    if not deps:
        raise HTTPException(404, "Dependency not found or not scanned yet")
    usage = dep_usage.get(key)
    return DependencyDetail.from_domain(deps[0], list(usage))
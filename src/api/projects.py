from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, status, Form
from fastapi.responses import JSONResponse

from ..domain.dependency import Dependency
from ..schemas.project import ProjectCreateResponse, ProjectSummary, ProjectDetail
from ..domain.project import Project, ScanState
from ..infra.storage import projects, dep_index, dep_usage
from ..services.tasks import scan_project
from ..utils.requirements_parser import parse_requirements

router = APIRouter(prefix="/projects")


@router.post("/", response_model=ProjectCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_project(
    name: str = Form('Untitled Project'),
    description: str = Form(''),
    requirements: UploadFile = File(..., description="requirements.txt"),
    background: BackgroundTasks = None,
):
    if requirements.filename != "requirements.txt":
        raise HTTPException(400, "File must be named requirements.txt")

    req_text = (await requirements.read()).decode()
    deps = [
        Dependency(name=n, version=v)
        for n, v in parse_requirements(req_text)
    ]
    
    project = Project(name=name, description=description, dependencies=deps)
    project_id = str(project.id)
    projects.add(project)
    for dep in deps:
        key = f"{dep.name.lower()}=={dep.version}"
        dep_index.add(dep)
        dep_usage.add_project(key, project_id)
    # kick off async scan in background
    background.add_task(scan_project, project_id)
    return ProjectCreateResponse.from_domain(project)


@router.get("/", response_model=list[ProjectSummary])
async def list_projects():
    return [ProjectSummary.from_domain(proj) for proj in projects.all()]


@router.get("/{project_id}", response_model=ProjectDetail)
async def project_detail(project_id: str):
    proj = projects.get(project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    if proj.status != ScanState.DONE:
        # 202 Accepted with Retry-After
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"detail": f"Scan not finished ({proj.status})."},
            headers={"Retry-After": "5"},
        )
    return ProjectDetail.from_domain(proj)

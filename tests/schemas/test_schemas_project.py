from src.schemas.project import ProjectSummary, ProjectDetail, ProjectCreateResponse
from src.domain.project import ScanState

def test_project_summary_fields():
    from uuid import uuid4
    summary = ProjectSummary(
        id=uuid4(),
        name='proj',
        status=ScanState.PENDING,
        vulnerable=False
    )
    assert summary.name == 'proj'
    assert summary.status == ScanState.PENDING

def test_project_detail_inherits_summary():
    from uuid import uuid4
    from src.schemas.dependency import DependencySummary
    dep_summary = DependencySummary(name='requests', version='2.25.1', vulnerable=False)
    detail = ProjectDetail(
        id=uuid4(),
        name='proj',
        status=ScanState.DONE,
        description='desc',
        vulnerable=True,
        dependencies=[dep_summary]
    )
    assert detail.name == 'proj'
    assert detail.status == ScanState.DONE
    assert detail.description == 'desc'
    assert dep_summary in detail.dependencies

def test_project_create_response():
    from uuid import uuid4
    resp = ProjectCreateResponse(id=uuid4(), name='proj', status=ScanState.PENDING)
    assert resp.name == 'proj'
    assert resp.status == ScanState.PENDING

from src.schemas.dependency import DependencySummary, DependencyDetail

def test_dependency_summary_fields():
    summary = DependencySummary(name='requests', version='2.25.1', vulnerable=False)
    assert summary.name == 'requests'
    assert summary.version == '2.25.1'
    assert summary.vulnerable is False

def test_dependency_detail_inherits_summary():
    from uuid import uuid4
    from src.schemas.dependency import Vulnerability
    project_ids = [uuid4()]
    vuln = Vulnerability(id='CVE-1234')
    detail = DependencyDetail(
        name='flask',
        version='1.1.2',
        vulnerable=True,
        usage_count=1,
        project_ids=project_ids,
        vulnerabilities=[vuln]
    )
    assert detail.name == 'flask'
    assert detail.vulnerable is True
    assert isinstance(detail.vulnerabilities, list)

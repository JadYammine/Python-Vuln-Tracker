import pytest

from src.domain.project import Project, ScanState
from src.domain.dependency import Dependency, Vulnerability

def test_project_equality():
    dep1 = Dependency(name='requests', version='2.25.1')
    dep2 = Dependency(name='flask', version='1.1.2')
    proj1 = Project(name='proj', dependencies=[dep1, dep2])
    proj2 = Project(name='proj', dependencies=[dep1, dep2])
    proj3 = Project(name='other', dependencies=[dep1])
    assert proj1.model_dump(exclude={'id'}) == proj2.model_dump(exclude={'id'})
    assert proj1.model_dump(exclude={'id'}) != proj3.model_dump(exclude={'id'})
    # Assert default ScanState
    assert proj1.status == ScanState.PENDING

def test_project_vulnerable_computed_field():
    # No vulnerable dependencies
    dep1 = Dependency(name='requests', version='2.25.1')
    dep2 = Dependency(name='flask', version='1.1.2')
    proj = Project(name='proj', dependencies=[dep1, dep2])
    assert proj.vulnerable is False
    # Add a vulnerable dependency
    vuln = Vulnerability(id='CVE-1234')
    dep2.vulnerabilities.append(vuln)
    proj_with_vuln = Project(name='proj', dependencies=[dep1, dep2])
    assert proj_with_vuln.vulnerable is True

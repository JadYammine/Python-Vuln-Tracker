
import pytest

from src.domain.dependency import Dependency
from src.domain.dependency import Vulnerability

def test_dependency_equality():
    dep1 = Dependency(name='requests', version='2.25.1')
    dep2 = Dependency(name='requests', version='2.25.1')
    dep3 = Dependency(name='flask', version='1.1.2')
    assert dep1 == dep2
    assert dep1 != dep3

def test_dependency_vulnerable_computed_field():
    dep = Dependency(name='requests', version='2.25.1')
    assert dep.vulnerable is False
    vuln = Vulnerability(id='CVE-1234')
    dep_with_vuln = Dependency(name='requests', version='2.25.1', vulnerabilities=[vuln])
    assert dep_with_vuln.vulnerable is True

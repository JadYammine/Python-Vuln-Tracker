from src.domain.project import Project
from src.domain.dependency import Dependency
from src.infra import storage

def test_add_and_get_project():
    dep = Dependency(name='requests', version='2.25.1')
    proj = Project(name='proj', dependencies=[dep])
    storage.projects.add(proj)
    retrieved = storage.projects.get(str(proj.id))
    assert retrieved.name == 'proj'
    assert dep in retrieved.dependencies
    # Check all projects
    assert any(p.name == 'proj' for p in storage.projects.all())
    # Add dependency to index and usage
    storage.dep_index.add(dep)
    key = f"{dep.name}=={dep.version}"
    storage.dep_usage.add_project(key, str(proj.id))
    assert dep in storage.dep_index.get(key)
    assert str(proj.id) in storage.dep_usage.get(key)

def test_project_storage_all():
    proj1 = Project(name='p1', dependencies=[])
    proj2 = Project(name='p2', dependencies=[])
    storage.projects.add(proj1)
    storage.projects.add(proj2)
    all_projects = list(storage.projects.all())
    assert any(p.name == 'p1' for p in all_projects)
    assert any(p.name == 'p2' for p in all_projects)

def test_dependency_index_all():
    dep1 = Dependency(name='d1', version='1.0')
    dep2 = Dependency(name='d2', version='2.0')
    storage.dep_index.add(dep1)
    storage.dep_index.add(dep2)
    all_deps = [d for deps in storage.dep_index.all() for d in deps]
    assert any(d.name == 'd1' for d in all_deps)
    assert any(d.name == 'd2' for d in all_deps)

def test_dependency_usage_add_and_get():
    dep_key = 'd3==3.0'
    proj_id = 'proj-uuid-123'
    storage.dep_usage.add_project(dep_key, proj_id)
    assert proj_id in storage.dep_usage.get(dep_key)
    # Should not raise error for missing key
    assert storage.dep_usage.get('nonexistent') == set()

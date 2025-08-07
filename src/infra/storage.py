from collections import defaultdict
from ..domain.project import Project
from ..domain.dependency import Dependency

class ProjectStorage:
    def __init__(self):
        self.projects: dict[str, Project] = {}

    def add(self, project: Project):
        self.projects[str(project.id)] = project

    def get(self, id: str) -> Project:
        return self.projects.get(id)

    def all(self):
        return self.projects.values()

class DependencyIndex:
    def __init__(self):
        self.dep_index: dict[str, list[Dependency]] = defaultdict(list)

    def add(self, dep: Dependency):
        self.dep_index[f"{dep.name}=={dep.version}"].append(dep)

    def get(self, name: str) -> list[Dependency]:
        return self.dep_index.get(name, [])

    def all(self):
        return self.dep_index.values()

class DependencyUsage:
    def __init__(self):
        self.dep_usage: dict[str, set[str]] = defaultdict(set)

    def add_project(self, dep_name: str, project_id: str):
        self.dep_usage[dep_name].add(project_id)

    def get(self, dep_name: str) -> set[str]:
        return self.dep_usage.get(dep_name, set())

# Singleton instances for compatibility
projects = ProjectStorage()
dep_index = DependencyIndex()
dep_usage = DependencyUsage()



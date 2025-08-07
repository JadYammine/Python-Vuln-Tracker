from src.utils.requirements_parser import parse_requirements

def test_parse_requirements_basic():
    content = """
    requests==2.25.1
    flask==1.1.2
    # comment
    numpy==1.19.5
    """
    result = list(parse_requirements(content))
    assert ("requests", "2.25.1") in result
    assert ("flask", "1.1.2") in result
    assert ("numpy", "1.19.5") in result
    assert len(result) == 3

def test_parse_requirements_ignores_invalid_lines():
    content = """
    -e git+https://github.com/user/repo.git#egg=repo
    somepackage>=1.0
    validpkg==0.1.0
    """
    result = list(parse_requirements(content))
    assert ("validpkg", "0.1.0") in result
    assert len(result) == 1

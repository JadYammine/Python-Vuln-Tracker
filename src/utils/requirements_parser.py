import re

REQ_LINE = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([^\s#]+)")

def parse_requirements(txt: str):
    """Yield (name, version) pairs from a requirements.txt string, skipping comments and blank lines."""
    for line in txt.splitlines():
        m = REQ_LINE.match(line)
        if m:
            yield m.group(1).lower(), m.group(2)

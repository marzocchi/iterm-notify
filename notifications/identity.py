from pathlib import Path


def load(path: Path) -> str:
    try:
        with open(file=str(path), mode='r') as f:
            first_line = f.readline().strip()
    except FileNotFoundError:
        raise RuntimeError("identify file not found")

    if first_line == "":
        raise RuntimeError("identity file is empty")

    return first_line

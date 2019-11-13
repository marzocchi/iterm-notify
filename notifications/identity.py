from pathlib import Path


def load_from_default_path() -> str:
    home = Path.home()
    return load(home.joinpath('.iterm-notify-identity'))


def load(path: Path) -> str:
    try:
        with open(file=str(path), mode='r') as f:
            first_line = f.readline().strip()
    except FileNotFoundError:
        raise RuntimeError("identify file not found")

    if first_line == "":
        raise RuntimeError("identity file is empty")

    return first_line

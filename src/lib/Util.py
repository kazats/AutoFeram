import shutil as sh
from pathlib import Path


def feram_path(fallback: Path = Path.cwd()) -> Path:
    which = sh.which('feram')

    return Path(which) if which is not None else fallback

def project_root() -> Path:
    return Path(__file__).parent.parent.parent

def src_root() -> Path:
    return Path(__file__).parent.parent

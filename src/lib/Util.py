import shutil as sh
from pathlib import Path


def feram_with_fallback(fallback: Path = Path.cwd()) -> Path:
    '''Use the Feram executable in $PATH, otherwise use fallback.'''
    which = sh.which('feram')

    return Path(which) if which else fallback

def project_root() -> Path:
    return Path(__file__).parent.parent.parent

def src_root() -> Path:
    return Path(__file__).parent.parent

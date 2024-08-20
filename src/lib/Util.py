import colors
import datetime
import shutil as sh
from pathlib import Path
from result import Result


def feram_with_fallback(fallback: Path = Path.cwd()) -> Path:
    '''Use the Feram executable in $PATH, otherwise use fallback.'''
    which = sh.which('feram')

    return Path(which) if which else fallback

def project_root() -> Path:
    return Path(__file__).parent.parent.parent

def src_root() -> Path:
    return Path(__file__).parent.parent

def colorize(result: Result):
    return colors.yellow(result) if result.is_ok() else colors.red(result)

def timestamp(format = '%Y-%m-%d'):
    return datetime.datetime.now().strftime(format)

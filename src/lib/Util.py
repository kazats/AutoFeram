import colors
import datetime
import shutil as sh
from pathlib import Path
from result import Result, Ok, Err


def feram_with_fallback(fallback: Path = Path.cwd()) -> Path:
    '''Use the Feram executable in $PATH, otherwise use fallback.'''
    which = sh.which('feram')

    return Path(which) if which else fallback

def project_root() -> Path:
    return Path(__file__).parent.parent.parent

def src_root() -> Path:
    return Path(__file__).parent.parent

def print_result(result: Result, color_ok='green', color_err='red', color_body='gray') -> None:
    match result:
        case Ok(value):
            print(f"{colors.color('Success', color_ok)}\t {colors.color(value, color_body)}")
        case Err(e):
            print(f"{colors.color('Failure', color_err)}\t {colors.color(e, color_body)}")

def timestamp(format = '%Y-%m-%d'):
    return datetime.datetime.now().strftime(format)

import colors
import datetime
import shutil as sh
import inspect
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

def caller_src_path():
    # adjust frame index if moved!
    return Path(inspect.stack()[2].filename)

def print_result(result: Result, color_ok='green', color_err='red', color_body='dimgray', text_ok='Success') -> None:
    match result:
        case Ok(value):
            print(f"{colors.color(text_ok, color_ok)}\t {colors.color(value, color_body)}")
        case Err(e):
            print(f"{colors.color('Failure', color_err)}\t {colors.color(e, color_body)}")

def timestamp(format = '%Y-%m-%d'):
    return datetime.datetime.now().strftime(format)

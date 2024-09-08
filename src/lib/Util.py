import argparse
import types
import colors
import datetime
import shutil as sh
import inspect
import sys
from pathlib import Path
from result import Result, Ok, Err
from typing import cast


def feram_with_fallback(fallback: Path = Path.cwd()) -> Path:
    '''Use the Feram executable in $PATH, otherwise use fallback.'''
    which = sh.which('feram')

    return Path(which) if which else fallback

def feram_bin_from_cmd_line():
    '''Use the feram executable provided by the command-line argument.
    Otherwise use the executable in $PATH.'''
    parser = argparse.ArgumentParser(prog='AutoFeram')
    parser.add_argument('-f', '--feram-bin')
    feram_bin_arg = parser.parse_args().feram_bin

    if feram_bin_arg:
        return Path(feram_bin_arg)
    elif feram_bin_which := sh.which('feram'):
        return Path(feram_bin_which)

def project_root() -> Path:
    return Path(__file__).parent.parent.parent

def src_root() -> Path:
    return Path(__file__).parent.parent

def caller_src_path():
    # adjust frame index if moved!
    return Path(inspect.stack()[2].filename)

def function_name():
    return cast(types.FrameType,
                cast(types.FrameType,
                     inspect.currentframe()).f_back).f_code.co_name

def print_result(result: Result, color_ok='green', color_err='red', color_body='dimgray', text_ok='Success') -> None:
    match result:
        case Ok(value):
            print(f"{colors.color(text_ok, color_ok)}\t {colors.color(value, color_body)}")
        case Err(e):
            msg = f"{colors.color('Failure', color_err)}\t {colors.color(e, color_body)}"
            print(msg)
            print(msg, file=sys.stderr)

def exit_from_result(result: Result):
    match result:
        case Ok(_):
            sys.exit()
        case Err(_):
            sys.exit(1)

def timestamp(format = '%Y-%m-%d'):
    return datetime.datetime.now().strftime(format)

import polars as pl
import subprocess as sub
import os
import shutil
import tarfile
import colors
from functools import reduce
from pathlib import Path
from enum import Enum
from result import Result, Ok, Err, as_result, do
from collections.abc import Callable, Iterator, Sequence
from typing import Any, Self, TypeAlias, cast

from src.lib.Util import project_root


safe_run = as_result(Exception)(sub.run)

def from_completed_process(completed_process: sub.CompletedProcess) -> Result[str, str]:
    if completed_process.returncode == 0:
        return Ok(completed_process.stdout)
    else:
        return Err(f'[{completed_process.returncode}] {completed_process.stderr}')

def rel_to_project_root(path: Path) -> Path:
    return path.relative_to(project_root())


PreconditionR: TypeAlias = Result[Path, str]
Precondition: TypeAlias = Callable[[Path], PreconditionR]

def file_exists(path: Path) -> PreconditionR:
    if path.is_file():
        return Ok(path)
    else:
        return Err(f'No such file: {path}.')

def dir_exists(path: Path) -> PreconditionR:
    if path.is_dir():
        return Ok(path)
    else:
        return Err(f'No such directory: {path}.')

def dir_doesnt_exist(path: Path) -> PreconditionR:
    if not path.exists():
        return Ok(path)
    else:
        return Err(f'Directory already exists: {path}.')


FilePathType = Enum('FilePathType', ['FileIn', 'FileOut', 'DirIn', 'DirOut'])

class FilePath():
    def __init__(self,
                 path: Path,
                 param_type: FilePathType,
                 preconditions: Sequence[Precondition]):
        self.path: Path = path
        self.param_type: FilePathType = param_type
        self.preconditions = preconditions

    def __repr__(self) -> str:
        return str(self.path)

    def check_preconditions(self) -> Result[Self, Sequence[str]]:
        checked = (cond(self.path) for cond in self.preconditions)
        failed = [x.unwrap_err() for x in checked if x.is_err()]
        if not failed:
            return Ok(self)
        else:
            return Err(failed)


class FileIn(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []):
        super().__init__(path, FilePathType.FileIn, [file_exists, *preconditions])

Exec: TypeAlias = FileIn

class FileOut(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []):
        super().__init__(path, FilePathType.FileOut, [*preconditions])

class DirIn(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []):
        super().__init__(path, FilePathType.DirIn, [dir_exists, *preconditions])

class DirOut(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []):
        super().__init__(path, FilePathType.DirOut, [*preconditions])


def print_result(result: Result, color_ok='green', color_err='red', color_body='gray') -> None:
    match result:
        case Ok(value):
            print(f"{colors.color('Success', color_ok)}\t {colors.color(value, color_body)}")
        case Err(e):
            print(f"{colors.color('Failure', color_err)}\t {colors.color(e, color_body)}")

OperationR: TypeAlias = Result[Any, str]
class Operation:
    def __init__(self, operation: Callable[[], OperationR]):
        self.operation = operation

    def __iter__(self) -> Iterator:
        return self.run().__iter__()

    def run(self) -> OperationR:
        res = self.operation()
        print_result(res)
        return res


class Empty(Operation):
    def __init__(self):
        pass

    def run(self) -> OperationR:
        return Ok(self.__class__.__name__)


class MkDirs(Operation):
    def __init__(self, path: DirOut):
        super().__init__(lambda: self.do(path))

    def do(self, path: DirOut) -> OperationR:
        return do(
            as_result(Exception)(checked.path.mkdir)(mode=0o755, parents=True, exist_ok=True)
            for checked in path.check_preconditions()
        ).map(lambda _: f'{self.__class__.__name__}: {path.path}').map_err(lambda x: f'{self.__class__.__name__}: {" ".join(cast(list[str], x))}')


class Cd(Operation):
    def __init__(self, dir: DirIn):
        super().__init__(lambda: self.do(dir))

    def do(self, dir: DirIn) -> OperationR:
        return do(
            as_result(OSError)(os.chdir)(checked.path)
            for checked in dir.check_preconditions()
        ).map(lambda _: f'{self.__class__.__name__}: {dir.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class WithDir(Operation):
    def __init__(self, cwd: DirIn, dir: DirIn, operation: Operation):
        super().__init__(lambda: self.do(cwd, dir, operation))

    def do(self, return_dir: DirIn, working_dir: DirIn, operation: Operation) -> OperationR:
        return do(
            Ok(dir_from)
            for _ in Cd(working_dir)
            for _ in operation
            for dir_from in Cd(return_dir)
        ).map(lambda _: f'{self.__class__.__name__}: {working_dir.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class Remove(Operation):
    def __init__(self, file: FileIn):
        super().__init__(lambda: self.do(file))

    def do(self, file: FileIn) -> OperationR:
        return do(
            as_result(Exception)(checked.path.unlink)()
            for checked in file.check_preconditions()
        ).map(lambda _: f'{self.__class__.__name__}: {file.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class Rename(Operation):
    def __init__(self, src: FileIn | DirIn, dst: FileOut | DirOut):
        super().__init__(lambda: self.do(src, dst))

    def do(self, src: FileIn | DirIn, dst: FileOut | DirOut) -> OperationR:
        return do(
            as_result(Exception)(checked_src.path.rename)(dst.path)
            for checked_src in src.check_preconditions()
        ).map(lambda _: f'{self.__class__.__name__}: {src.path} >> {dst.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class Cat(Operation):
    def __init__(self, path: FileIn):
        super().__init__(lambda: self.do(path))

    def do(self, file: FileIn) -> OperationR:
        return do(
            Ok(res)
            for checked in file.check_preconditions()
            for res in from_completed_process(
                sub.run(['cat', checked.path],
                        capture_output=True,
                        universal_newlines=True))
        ).map(lambda _: f'{self.__class__.__name__}: {file.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')
        # return do(
        #     Ok(res)
        #     for checked in file.check_preconditions()
        #     for completed_process in safe_run(['at', checked.path], capture_output=True, universal_newlines=True)
        #     for res in from_completed_process(completed_process)
        # ).map(lambda x: f'Cat: {x}')


class Copy(Operation):
    def __init__(self, src: FileIn, dst: FileOut):
        super().__init__(lambda: self.do(src, dst))

    def do(self, src: FileIn, dst: FileOut) -> OperationR:
        return do(
            as_result(OSError)(shutil.copy2)(checked_src.path, dst.path)
            for checked_src in src.check_preconditions()
        ).map(lambda _: f'{self.__class__.__name__}: {src.path} >> {dst.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class Append(Operation):
    def __init__(self, path_in: FileIn, path_out: FileOut):
        super().__init__(lambda: self.do(path_in, path_out))

    @as_result(Exception)
    def safe_append(self, path_in: FileIn, path_out: FileOut):
        with open(path_out.path, 'a') as outf:
            outf.write(path_in.path.read_text())

    def do(self, path_in: FileIn, path_out: FileOut) -> OperationR:
        return do(
            Ok(res)
            for checked_in in path_in.check_preconditions()
            for checked_out in path_out.check_preconditions()
            for res in self.safe_append(checked_in, checked_out)
        ).map(lambda _: f'{self.__class__.__name__}: {path_in.path} >> {path_out.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class Write(Operation):
    def __init__(self, file: FileOut, get_content: Callable[[], str]):
        super().__init__(lambda: self.do(file, get_content))

    @as_result(Exception)
    def safe_write(self, file: FileOut, content: str):
        file.path.write_text(content)
        # with open(file.path, 'w') as outf:
        #     outf.write(content)

    def do(self, file: FileOut, get_content: Callable[[], str]) -> OperationR:
        return do(
            self.safe_write(checked_out, get_content())
            for checked_out in file.check_preconditions()
        ).map(lambda _: f'{self.__class__.__name__}: {file.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class WriteParquet(Operation):
    def __init__(self, file: FileOut, get_df: Callable[[], pl.DataFrame]):
        super().__init__(lambda: self.do(file, get_df))

    @as_result(Exception)
    def safe_write_parquet(self, file: FileOut, df: pl.DataFrame) -> None:
        df.write_parquet(file.path)

    def do(self, file: FileOut, get_df: Callable[[], pl.DataFrame]) -> OperationR:
        return do(
            self.safe_write_parquet(checked_out, get_df())
            # TODO: check input files
            for checked_out in file.check_preconditions()
        ).map(lambda _: f'{self.__class__.__name__}: {file.path}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class Archive(Operation):
    def __init__(self, src: DirIn | FileIn, dst: FileOut):
        super().__init__(lambda: self.do(src, dst))

    @as_result(Exception)
    def safe_archive(self, src, dst) -> None:
        with tarfile.open(dst.path, 'w:gz') as tar:
            tar.add(src.path, arcname=src.path.name)

    def do(self, src, dst) -> OperationR:
        return do(
            Ok(res)
            for checked_src in src.check_preconditions()
            for checked_dst in dst.check_preconditions()
            for res in self.safe_archive(checked_src, checked_dst)
        ).map(lambda _: f'{self.__class__.__name__}: {src.path} >> {dst.path}')\
        .map_err(lambda x: f'{self.__class__.__name__}: {x}')


class Feram(Operation):
    def __init__(self, feram_bin: Exec, feram_input: FileIn):
        super().__init__(lambda: self.do(feram_bin, feram_input))

    def do(self, feram_bin: Exec, feram_input: FileIn) -> OperationR:
        return do(
            Ok(res)
            for checked_feram_bin in feram_bin.check_preconditions()
            for checked_feram_input in feram_input.check_preconditions()
            for res in from_completed_process(
                sub.run([checked_feram_bin.path, checked_feram_input.path]))
                # sub.run([checked_feram_bin.path, checked_feram_input.path],
                #         capture_output=True,
                #         universal_newlines=True))
        ).map(lambda _: f'{self.__class__.__name__}').map_err(lambda x: f'{self.__class__.__name__}: {x}')


class OperationSequence(Operation):
    def __init__(self, operations: Sequence[Operation] = []):
        self.operations = operations

    def run(self) -> OperationR:
        return reduce(lambda op, next_op: op.and_then(lambda _: next_op.run()),
                      self.operations,
                      Empty().run())

    def __iter__(self) -> Iterator:
        yield self.run()
        # return iter(self.operations)

    def __add__(self, other):
        return OperationSequence(self.operations + other.operations)

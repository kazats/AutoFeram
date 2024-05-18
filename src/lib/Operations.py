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
from collections.abc import Callable, Sequence
from typing import Any, Self, TypeAlias

from src.lib.Util import src_root


safe_run = as_result(Exception)(sub.run)

def from_completed_process(completed_process: sub.CompletedProcess) -> Result[str, str]:
    if completed_process.returncode == 0:
        return Ok(completed_process.stdout)
    else:
        return Err(f'[{completed_process.returncode}] {completed_process.stderr}')


def relative_to_cwd(path: Path) -> Path:
    # return path
    return path.relative_to(Path.cwd())


PreconditionReturn: TypeAlias = Result[Path, str]
Precondition: TypeAlias = Callable[[Path], PreconditionReturn]

def file_exists(path: Path) -> PreconditionReturn:
    if os.path.isfile(path):
        return Ok(path)
    else:
        return Err(f"No such file: {relative_to_cwd(path)}")

def dir_exists(path: Path) -> PreconditionReturn:
    if os.path.isdir(path):
        return Ok(path)
    else:
        return Err(f"No such directory: {relative_to_cwd(path)}")


FilePathType = Enum('FilePathType', ['FileIn', 'FileOut', 'DirIn', 'DirOut'])

class FilePath():
    def __init__(self,
                 path: Path,
                 param_type: FilePathType,
                 preconditions: Sequence[Precondition]) -> None:
        self.path: Path = path
        self.param_type: FilePathType = param_type
        self.preconditions = preconditions

    def __repr__(self) -> str:
        return str(relative_to_cwd(self.path))

    def check_preconditions(self) -> Result[Self, Sequence[str]]:
        checked = (cond(self.path) for cond in self.preconditions)
        failed = [x.unwrap_err() for x in checked if x.is_err()]
        if not failed:
            return Ok(self)
        else:
            return Err(failed)


class FileIn(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []) -> None:
        super().__init__(path, FilePathType.FileIn, [file_exists, *preconditions])

Exec: TypeAlias = FileIn

class FileOut(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []) -> None:
        super().__init__(path, FilePathType.FileOut, [*preconditions])

class DirIn(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []) -> None:
        super().__init__(path, FilePathType.DirIn, [dir_exists, *preconditions])

class DirOut(FilePath):
    def __init__(self, path: Path, preconditions: Sequence[Precondition] = []) -> None:
        super().__init__(path, FilePathType.DirOut, [*preconditions])


class Operation:
    def __init__(self, operation: Callable[[], Result[Any, str]]) -> None:
        self.operation = operation

    def run(self) -> Result[Any, str]:
        res = self.operation()
        color_res = colors.color(res, 'gray') if res.is_ok() else colors.red(res)
        print(color_res)
        return res


class Empty(Operation):
    def __init__(self) -> None:
        super().__init__(lambda: self.do())

    def do(self) -> Result[Any, str]:
        return Ok(f"Empty: 😄")


class MkDirs(Operation):
    def __init__(self, path: DirOut) -> None:
        super().__init__(lambda: self.do(path))

    def do(self, path: DirOut) -> Result[Any, str]:
        os.makedirs(path.path, mode=0o755, exist_ok=True)
        return Ok(f"MkDir: '{relative_to_cwd(path.path)}'")


class Cd(Operation):
    def __init__(self, dir: DirIn) -> None:
        super().__init__(lambda: self.do(dir))

    def do(self, dir: DirIn) -> Result[Any, str]:
        return do(
            as_result(OSError)(os.chdir)(checked.path)
            for checked in dir.check_preconditions()
        ).map(lambda _: f'Cd: {dir.path}').map_err(lambda x: f'Cd: {str(x)}')


class WithDir(Operation):
    def __init__(self, cwd: DirIn, dir: DirIn, operation: Operation) -> None:
        super().__init__(lambda: self.do(cwd, dir, operation))

    def do(self, return_dir: DirIn, working_dir: DirIn, operation: Operation) -> Result[Any, str]:
        return do(
            Ok(dir_from)
            for _ in Cd(working_dir).run()
            for _ in operation.run()
            for dir_from in Cd(return_dir).run()
        ).map(lambda _: f'WithDir: {relative_to_cwd(working_dir.path)}').map_err(lambda x: f'WithDir: {str(x)}')


class Remove(Operation):
    def __init__(self, file: FileIn) -> None:
        super().__init__(lambda: self.do(file))

    def do(self, file: FileIn) -> Result[Any, str]:
        return do(
            as_result(OSError)(os.remove)(checked.path)
            for checked in file.check_preconditions()
        ).map(lambda _: f'Remove: {relative_to_cwd(file.path)}').map_err(lambda x: f'Remove: {str(x)}')


class Rename(Operation):
    def __init__(self, src: FileIn | DirIn, dst: FileOut | DirOut) -> None:
        super().__init__(lambda: self.do(src, dst))

    def do(self, src: FileIn | DirIn, dst: FileOut | DirOut) -> Result[Any, str]:
        return do(
            as_result(OSError)(os.rename)(checked_src.path, dst.path)
            for checked_src in src.check_preconditions()
        ).map(lambda _: f'Rename: {relative_to_cwd(src.path)} >> {relative_to_cwd(dst.path)}').map_err(lambda x: f'Rename: {str(x)}')


class Cat(Operation):
    def __init__(self, path: FileIn) -> None:
        super().__init__(lambda: self.do(path))

    def do(self, file: FileIn) -> Result[Any, str]:
        return do(
            Ok(res)
            for checked in file.check_preconditions()
            for res in from_completed_process(
                sub.run(['cat', checked.path],
                        capture_output=True,
                        universal_newlines=True))
        ).map(lambda _: f'Cat: {relative_to_cwd(file.path)}').map_err(lambda x: f'Cat: {x}')
        # return do(
        #     Ok(res)
        #     for checked in file.check_preconditions()
        #     for completed_process in safe_run(['at', checked.path], capture_output=True, universal_newlines=True)
        #     for res in from_completed_process(completed_process)
        # ).map(lambda x: f'Cat: {x}')


class Copy(Operation):
    def __init__(self, src: FileIn, dst: FileOut) -> None:
        super().__init__(lambda: self.do(src, dst))

    def do(self, src: FileIn, dst: FileOut) -> Result[Any, str]:
        return do(
            as_result(OSError)(shutil.copy2)(checked_src.path, dst.path)
            for checked_src in src.check_preconditions()
        ).map(lambda _: f'Copy: {relative_to_cwd(src.path)} >> {relative_to_cwd(dst.path)}').map_err(lambda x: f'Copy: {str(x)}')


class Append(Operation):
    def __init__(self, path_in: FileIn, path_out: FileOut) -> None:
        super().__init__(lambda: self.do(path_in, path_out))

    @as_result(Exception)
    def safe_append(self, path_in: FileIn, path_out: FileOut):
        with open(path_in.path, 'r') as inf,\
            open(path_out.path, 'a') as outf:
            outf.write(inf.read())

    def do(self, path_in: FileIn, path_out: FileOut) -> Result[Any, str]:
        return do(
            Ok(res)
            for checked_in in path_in.check_preconditions()
            for checked_out in path_out.check_preconditions()
            for res in self.safe_append(checked_in, checked_out)
        ).map(lambda _: f"Append: {relative_to_cwd(path_in.path)} >> {relative_to_cwd(path_out.path)}").map_err(lambda x: f'Append: {x}')


class Write(Operation):
    def __init__(self, file: FileOut, get_content: Callable[[], str]) -> None:
        super().__init__(lambda: self.do(file, get_content))

    @as_result(Exception)
    def safe_write(self, file: FileOut, content: str):
        with open(file.path, 'w') as outf:
            outf.write(content)

    def do(self, file: FileOut, get_content: Callable[[], str]) -> Result[Any, str]:
        return do(
            Ok(res)
            for checked_out in file.check_preconditions()
            for res in self.safe_write(checked_out, get_content())
        ).map(lambda _: f"Write: {relative_to_cwd(file.path)}").map_err(lambda x: f'Write: {x}')


class WriteParquet(Operation):
    def __init__(self, file: FileOut, get_df: Callable[[], pl.DataFrame]) -> None:
        super().__init__(lambda: self.do(file, get_df))

    @as_result(Exception)
    def safe_write_parquet(self, file: FileOut, df: pl.DataFrame):
        df.write_parquet(file.path)

    def do(self, file: FileOut, get_df: Callable[[], pl.DataFrame]) -> Result[Any, str]:
        return do(
            Ok(res)
            # TODO: check input files
            for checked_out in file.check_preconditions()
            for res in self.safe_write_parquet(checked_out, get_df())
        ).map(lambda _: f"WriteParquet: {relative_to_cwd(file.path)}").map_err(lambda x: f'WriteParquet: {x}')


class Archive(Operation):
    def __init__(self, src: DirIn | FileIn, dst: FileOut) -> None:
        super().__init__(lambda: self.do(src, dst))

    @as_result(Exception)
    def safe_archive(self, src, dst):
        with tarfile.open(dst.path, "w:gz") as tar:
            tar.add(src.path, arcname=src.path.name)

    def do(self, src, dst) -> Result[Any, str]:
        return do(
            Ok(res)
            for checked_src in src.check_preconditions()
            for checked_dst in dst.check_preconditions()
            for res in self.safe_archive(checked_src, checked_dst)
        ).map(lambda _: f"Archive: {relative_to_cwd(src.path)} >> {relative_to_cwd(dst.path)}")\
        .map_err(lambda x: f'Archive: {x}')


class Feram(Operation):
    def __init__(self, feram_bin: Exec, feram_input: FileIn) -> None:
        super().__init__(lambda: self.do(feram_bin, feram_input))

    def do(self, feram_bin: Exec, feram_input: FileIn):
        return do(
            Ok(res)
            for checked_feram_bin in feram_bin.check_preconditions()
            for checked_feram_input in feram_input.check_preconditions()
            for res in from_completed_process(
                sub.run([checked_feram_bin.path, checked_feram_input.path]))
                # sub.run([checked_feram_bin.path, checked_feram_input.path],
                #         capture_output=True,
                #         universal_newlines=True))
        ).map(lambda _: f'Feram: success').map_err(lambda x: f'Feram: {x}')


class OperationSequence:
    def __init__(self, operations: Sequence[Operation] = []) -> None:
        self.operations = operations

    def run(self) -> Result[Any, str]:
        return reduce(lambda op, next_op: op.and_then(lambda _: next_op.run()),
                      self.operations[1:],
                      self.operations[0].run())

    def __iter__(self):
        return iter(self.operations)

    def __add__(self, other):
        return OperationSequence(self.operations + other.operations)


if __name__ == "__main__":
    # FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'
    # FERAM_BIN = Path(cast(str, shutil.which('feram')))

    # Feram(Exec(FERAM_BIN), FileIn(Path('test.feram')))

    test_path = src_root() / 'test' / 'file_operations'
    test_file = test_path / 'test'
    test_dir  = test_path / 'dir'

    operations: Sequence[Operation] = [
        MkDirs(DirOut(test_dir)),
        WithDir(DirIn(test_path), DirIn(test_dir),
                Append(FileIn(test_file),
                       FileOut(test_dir / 'dir_test'))),
        Append(FileIn(test_file),
               FileOut(test_path / 'append')),
        Copy(FileIn(test_path / 'append'),
               FileOut(test_path / 'rename')),
        # Remove(FileIn(test_path/'rename'))
    ]

    OperationSequence(operations).run()

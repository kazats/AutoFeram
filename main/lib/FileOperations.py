import subprocess as sub
import os
from pathlib import Path
from collections.abc import Callable
from typing import Any, Self, TypeAlias
from enum import Enum
from result import Result, Ok, Err, as_result, do


safe_run = as_result(Exception)(sub.run)

def from_completed_process(completed_process: sub.CompletedProcess) -> Result[str, str]:
    if completed_process.returncode == 0:
        return Ok(completed_process.stdout)
    else:
        return Err(f'[{completed_process.returncode}] {completed_process.stderr}')


def relative_to_cwd(path: Path) -> Path:
    return path.relative_to(Path.cwd())


PreconditionReturn: TypeAlias = Result[Path, str]
Precondition: TypeAlias = Callable[[Path], PreconditionReturn]

def file_exists(path: Path) -> PreconditionReturn:
    if os.path.isfile(path):
        return Ok(path)
    else:
        return Err(f"File '{relative_to_cwd(path)}' doesn't exist")

def dir_exists(path: Path) -> PreconditionReturn:
    if os.path.isdir(path):
        return Ok(path)
    else:
        return Err(f"Directory '{relative_to_cwd(path)}' doesn't exist")


FilePathType = Enum('FilePathType', ['FileIn', 'FileOut', 'DirIn', 'DirOut'])

class FilePath():
    def __init__(self,
                 path: Path,
                 param_type: FilePathType,
                 preconditions: list[Precondition]) -> None:
        self.path: Path = path
        self.param_type: FilePathType = param_type
        self.preconditions = preconditions

    def __repr__(self) -> str:
        return str(relative_to_cwd(self.path))

    def check_preconditions(self) -> Result[Self, list[str]]:
        checked = (cond(self.path) for cond in self.preconditions)
        failed = [x.unwrap_err() for x in checked if x.is_err()]
        if not failed:
            return Ok(self)
        else:
            return Err(failed)


class FileIn(FilePath):
    def __init__(self, path: Path, preconditions: list[Precondition] = []) -> None:
        super().__init__(path, FilePathType.FileIn, [file_exists, *preconditions])

class FileOut(FilePath):
    def __init__(self, path: Path, preconditions: list[Precondition] = []) -> None:
        super().__init__(path, FilePathType.FileOut, [*preconditions])

class DirIn(FilePath):
    def __init__(self, path: Path, preconditions: list[Precondition] = []) -> None:
        super().__init__(path, FilePathType.DirIn, [dir_exists, *preconditions])

class DirOut(FilePath):
    def __init__(self, path: Path, preconditions: list[Precondition] = []) -> None:
        super().__init__(path, FilePathType.DirOut, [*preconditions])


class FileOperation:
    def __init__(self, operation: Callable[[], Result[Any, str]]) -> None:
        self.operation = operation

    def run(self):
        result = self.operation()
        print(result)


class Cat(FileOperation):
    def __init__(self, path: FileIn) -> None:
        super().__init__(lambda: self.do(path))

    def do(self, file: FileIn) -> Result[Any, str]:
        return do(
            Ok(res)
            for checked in file.check_preconditions()
            for res in from_completed_process(sub.run(['cat', checked.path], capture_output=True, universal_newlines=True))
        ).map(lambda x: f'Cat: {x}')
        # return do(
        #     Ok(res)
        #     for checked in file.check_preconditions()
        #     for completed_process in safe_run(['at', checked.path], capture_output=True, universal_newlines=True)
        #     for res in from_completed_process(completed_process)
        # ).map(lambda x: f'Cat: {x}')


class MkDirs(FileOperation):
    def __init__(self, path: DirOut) -> None:
        super().__init__(lambda: self.do(path))

    def do(self, path: DirOut) -> Result[Any, str]:
        os.makedirs(path.path, mode=0o755, exist_ok=True)
        return Ok(f"MkDir: '{relative_to_cwd(path.path)}'")


class Append(FileOperation):
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
        ).map(lambda x: f"Append: '{relative_to_cwd(path_in.path)}' >> '{relative_to_cwd(path_out.path)}'")


if __name__ == "__main__":
    Cat(FileIn(Path.cwd() / 'test')).run()
    MkDirs(DirOut(Path.cwd() / 'dir' / 'dir2')).run()
    Append(FileIn(Path.cwd() / 'test'),
           FileOut(Path.cwd() / 'append')).run()

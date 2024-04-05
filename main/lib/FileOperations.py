import subprocess as sub
import os
from pathlib import Path
from collections.abc import Callable
from typing import Any, Concatenate, ParamSpec, TypeVar
from enum import Enum
from result import Result, Ok, Err


FilePathType = Enum('FilePathType', ['In', 'Out', 'Dir'])

class FilePath():
    def __init__(self, path: Path, param_type: FilePathType) -> None:
        self.path: Path = path
        self.param_type: FilePathType = param_type

    def __repr__(self) -> str:
        return str(self.path.relative_to(Path.cwd()))


class FileIn(FilePath):
    def __init__(self, path: Path) -> None:
        super().__init__(path, FilePathType.In)


class FileOut(FilePath):
    def __init__(self, path: Path) -> None:
        super().__init__(path, FilePathType.Out)


class Dir(FilePath):
    def __init__(self, path: Path) -> None:
        super().__init__(path, FilePathType.Dir)


class FileOperation:
    def __init__(self, operation: Callable[[], Result[Any, str]]) -> None:
        self.operation = operation

    def run(self):
        result = self.operation()
        match result:
            case Ok(message):
                print(message)
            case Err(error):
                print(error)


class Echo(FileOperation):
    def __init__(self, path: FileIn) -> None:
        super().__init__(lambda: self.echo(path))

    def echo(self, file: FileIn) -> Result[Any, str]:
        sub.run(['nu', '-c', f'open {file.path}'])
        return Ok(f'echoed contents of "{file}"')


class MkDir(FileOperation):
    def __init__(self, path: Dir) -> None:
        super().__init__(lambda: self.mkdir(path))

    def mkdir(self, path: Dir) -> Result[Any, str]:
        os.makedirs(path.path, exist_ok=True)
        return Ok(f'created directory "{path}"')


class Append(FileOperation):
    def __init__(self, path_in: FileIn, path_out: FileOut) -> None:
        super().__init__(lambda: self.append(path_in, path_out))

    def append(self, path_in: FileIn, path_out: FileOut) -> Result[Any, str]:
        with open(path_in.path, 'r') as inf,\
            open(path_out.path, 'a') as outf:
            outf.write(inf.read())
        return Ok(f'appended contents of "{path_in}" to "{path_out}"')


if __name__ == "__main__":
    Echo(FileIn(Path.cwd() / 'test')).run()
    MkDir(Dir(Path.cwd() / 'dir' / 'dir2')).run()
    Append(FileIn(Path.cwd() / 'test'),
           FileOut(Path.cwd() / 'append')).run()

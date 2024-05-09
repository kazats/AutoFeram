from typing import Generic, NamedTuple, TypeVar


BoltzmannConst: float = 8.617e-5


T1 = TypeVar('T1')

class Vec3(NamedTuple, Generic[T1]):
    x: T1
    y: T1
    z: T1

    def __str__(self) -> str:
        return f'{self.x} {self.y} {self.z}'

class Vec7(NamedTuple, Generic[T1]):
    x1: T1
    x2: T1
    x3: T1
    x4: T1
    x5: T1
    x6: T1
    x7: T1

    def __str__(self) -> str:
        return ' '.join(map(str, self))

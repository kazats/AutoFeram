#!/usr/bin/env python
# author: Lan-Tien Hsu


'''
Define your domain seeds (variables called "Domain", imagine a seed where a specific domain starts to grow) and the electric field in xyz direction (variables called "Props") in the __main__ function in the domain_rectangle.py.
'''

from typing import Any, List, Tuple, Dict, Iterator, Optional
from dataclasses import dataclass, astuple
from collections import Counter
import numpy as np


Vec3 = Tuple[int, int, int]


@dataclass(frozen=True)
class Props:
    x: float
    y: float
    z: float

    def __iter__(self) -> Iterator[Any]:
        return iter(astuple(self))

    def __repr__(self):
        return f"(Prop {self.x} {self.y} {self.z})"


@dataclass(frozen=True)
class Domain:
    seed: Vec3
    props: Props

    def __repr__(self):
        return f"(Domain {self.seed} {self.props})"


@dataclass
class Point:
    domain: Domain
    boundary: Optional[float] = None

    def __repr__(self):
        return f"(Point {self.domain} {self.boundary})"


@dataclass
class System:
    size: Vec3
    points: Dict[Vec3, Point]

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self) -> Iterator[Tuple[Vec3, Point]]:
        return iter(self.points.items())

    def __getitem__(self, coord: Vec3) -> Point:
        return self.points[coord]

    def find_neighbors(self, coord: Vec3, d: int) -> List[Tuple[Vec3, Point]]:
        """right now, it only works for d = 1"""

        """
        the points at the boundary of the system
        (e.g. (0,0,0), (SIZE,SIZE,SIZE)) are just not considered
        as neighbors of the point. Because of this the points at
        the system boundary will never be found/set as domain boundary.
        If it is intended to make these points as domain boundary,
        then we can just write these points to the .defects in the end.
        """
        """
        # if x==0 or y==0 or z==0 or x==size or y==size or z==size:
        #     return [[x+d,y,z],[x-d,y,z],[x,y+d,z],[x,y-d,z],[x,y,z+d],[x,y,z-d]]

        * think how to deal with point at the boundary of the system
        under periodic boundary condition : probably not needed
        """

        x, y, z = coord
        coords: List[Vec3] = [
            (x - d, y, z),
            (x, y - d, z),
            (x, y, z - d),
            (x + d, y, z),
            (x, y + d, z),
            (x, y, z + d),
        ]

        return [
            (coord, self[coord])
            for coord in coords
            if all(c >= 0 for c in coord)
                and all(coord[i] < self.size[i] for i in range(len(self.size)))
        ]

    def find_most_common_grain(self, coord: Vec3, d: int) -> Tuple[Domain, float]:
        """float: is the percentage of the majority domain"""

        neighbors: List[Tuple[Vec3, Point]] = self.find_neighbors(coord, d)

        neighbor_grains: List[Domain] = [n[1].domain for n in neighbors]

        neighbor_grain_count = Counter(neighbor_grains)

        max_grain = neighbor_grain_count.most_common(1)[0]

        return (max_grain[0], max_grain[1] / neighbor_grain_count.total())

    def find_boundary(self, coord: Vec3, d: int) -> Tuple[Domain, float]:
        return self.find_most_common_grain(coord, d)


def find_closest_grain(grains: List[Domain], coord: Vec3) -> Domain:
    def distance(p1: Vec3, p2: Vec3) -> np.floating:
        return np.linalg.norm(np.fromiter(p1, int) - np.fromiter(p2, int))

    return min(
        map(lambda domain: (domain, distance(domain.seed, coord)), grains),
        key=lambda x: float(x[1]),
    )[0]


def generate_coords(size: Vec3) -> List[Vec3]:
    size_x, size_y, size_z = map(range, size)
    return [(x, y, z) for x in size_x for y in size_y for z in size_z]


def find_boundaries(size: Vec3, grains: List[Domain]) -> Dict[Vec3, Point]:
    coords: List[Vec3] = generate_coords(size)
    system: System = System(
        size,
        {coord: Point(find_closest_grain(grains, coord), None) for coord in coords},
    )

    boundaries = {
        coord: Point(*system.find_boundary(coord, 1)) for coord in system.points.keys()
    }

    return boundaries


def bto_localfield(system: Dict[Vec3, Point]):
    with open("bto.localfield", "w") as f:
        for coord, point in system.items():
            x, y, z = coord
            px, py, pz = point.domain.props
            f.write(f"{x} {y} {z} {px} {py} {pz}\n")


def bto_defects(system: Dict[Vec3, Point]):
    with open("bto.defects", "w") as f:
        for coord, point in system.items():
            x, y, z = coord
            px, py, pz = point.domain.props

            if point.boundary != None and point.boundary < 1:
                f.write(f"{x} {y} {z} {px * 134.106} {py} {pz}\n")


if __name__ == "__main__":

    size = (48, 96, 48)

    grains = [
        Domain((24, 0, 0), Props(-1, 0, 0)),
        Domain((0, 48, 0), Props(0, 1, 0)),
        Domain((24, 95, 0), Props(1, 0, 0)),
        Domain((48, 48, 0), Props(0, -1, 0)),
    ]

    system = find_boundaries(size, grains)

    [ f(system) for f in [bto_localfield, bto_defects] ]


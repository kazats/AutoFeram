#!/usr/bin/env python
# author: Lan-Tien Hsu

# python version: 3.11.8 (higher than 3.10 should work)
'''
Define your domain seeds (variables called "Domain", imagine a seed where a specific domain starts to grow)
and the electric field in xyz direction (variables called "Props") in the __main__ section.
'''

import numpy as np
import operator as op
from collections.abc import Sequence
from pathlib import Path
from dataclasses import dataclass
from collections import Counter
from typing import NamedTuple, TypeAlias, Iterator, Optional
from itertools import accumulate

from src.lib.common import Vec3
from src.lib.Util import project_root


Int3:  TypeAlias = Vec3[int]
Props: TypeAlias = Vec3[float]

class Domain(NamedTuple):
    seed: Int3
    props: Props

class PointProps(NamedTuple):
    domain: Domain
    boundary: Optional[float] = None

Point:    TypeAlias = tuple[Int3, PointProps]
PointMap: TypeAlias = dict[Int3, PointProps]

@dataclass
class System:
    size: Int3
    points: PointMap

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self) -> Iterator[Point]:
        return iter(self.points.items())

    def __getitem__(self, coord: Int3) -> PointProps:
        return self.points[coord]

    def find_neighbors(self, coord: Int3, d: int) -> list[Point]:
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
        coords: list[Int3] = [
            Int3(x - d, y, z),
            Int3(x, y - d, z),
            Int3(x, y, z - d),
            Int3(x + d, y, z),
            Int3(x, y + d, z),
            Int3(x, y, z + d),
        ]

        return [
            (coord, self[coord])
            for coord in coords
            if all(c >= 0 for c in coord)
                and all(coord[i] < self.size[i] for i in range(len(self.size)))
        ]

    def find_boundary(self, coord: Int3, d: int) -> tuple[Domain, float]:
        """float: is the percentage of the majority domain"""

        neighbors: Sequence[Point]    = self.find_neighbors(coord, d)
        neighbor_grains: list[Domain] = [n[1].domain for n in neighbors]
        neighbor_grain_count          = Counter(neighbor_grains)
        max_grain                     = neighbor_grain_count.most_common(1)[0]

        return (max_grain[0], max_grain[1] / neighbor_grain_count.total())


def find_closest_grain(domains: list[Domain], coord: Int3) -> Domain:
    def distance(p1: Int3, p2: Int3) -> np.floating:
        return np.linalg.norm(np.fromiter(p1, int) - np.fromiter(p2, int))

    return min(
        map(lambda domain: (domain, distance(domain.seed, coord)),
            domains),
        key=lambda x: x[1],
    )[0]


def generate_coords(size: Int3) -> list[Int3]:
    size_x, size_y, size_z = map(range, size)
    return [
        Int3(x, y, z)
        for x in size_x
        for y in size_y
        for z in size_z
    ]


def find_boundaries(size: Int3, grains: list[Domain]) -> PointMap:
    coords: list[Int3] = generate_coords(size)
    system: System = System(
        size,
        {coord: PointProps(find_closest_grain(grains, coord), None) for coord in coords},
    )

    boundaries = {
        coord: PointProps(*system.find_boundary(coord, 1)) for coord in system.points.keys()
    }

    return boundaries


def write_bto_localfield(dir_out: Path, system: PointMap):
    with open(dir_out / 'bto.localfield', 'w') as f:
        for coord, point in system.items():
            x, y, z = coord
            px, py, pz = point.domain.props
            f.write(f'{x} {y} {z} {px} {py} {pz}\n')


def write_bto_defects(dir_out: Path, system: PointMap):
    with open(dir_out / 'bto.defects', 'w') as f:
        for coord, point in system.items():
            x, y, z = coord
            px, py, pz = point.domain.props

            if point.boundary and point.boundary < 1:
                f.write(f'{x} {y} {z} {px * 134.106} {py} {pz}\n')

def assign_modulation(z: int, bto_sto: tuple[int, int]):
    bto_sto_acc = list(accumulate(bto_sto, op.add))
    z_redu      = z % bto_sto_acc[-1]

    if z_redu < bto_sto_acc[0]:
        return 8 # bto
    elif bto_sto_acc[0] <= z_redu < bto_sto_acc[1]:
        return -8 # sto

def write_bto_modulation(dir_out: Path, size: Int3, coords: list[Int3], bto_sto: tuple[int, int]):
    with open(dir_out / 'bto.modulation', 'w') as f:
        for (x, y, z) in coords:
            f.write(f'{x} {y} {z} {assign_modulation(z, bto_sto)}\n')

if __name__ == '__main__':
    working_dir = project_root() / 'output' / 'domain'

    size = Int3(2, 1, 6)

    grains = [
        Domain(Int3(0, 0, 0), Props(0, 0, 0)),
        # Domain(Int3(0, 2, 0), Props(0, 1, 0)),
        # Domain(Int3(12, 47, 0), Props(1, 0, 0)),
        # Domain(Int3(24, 24, 0), Props(0, -1, 0)),
    ]

    system = find_boundaries(size, grains)

    ##### get .modulation: for superlattices
    BTO_STO = (1, 2)
    write_bto_modulation(working_dir, size, generate_coords(size), BTO_STO)

    ##### get .localfield and .defects: for multidomains
    [ f(working_dir, system) for f in [write_bto_localfield, write_bto_defects] ]

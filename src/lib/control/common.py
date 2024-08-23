import polars as pl
from dataclasses import dataclass, fields
from pathlib import Path
from typing import NamedTuple
from collections.abc import Mapping, Sequence

from src.lib.Config import FeramConfig, Material, Setup, SetupDict, merge_setups


class Runner(NamedTuple):
    sim_name: str
    working_dir: Path
    feram_path: Path


class TempRange(NamedTuple):
    initial: int
    final: int
    delta: int

@dataclass
class TempConfig:
    def __init__(self, material: Material, temp_range: TempRange, setup: Sequence[Setup]) -> None:
        self.material = material
        self.temp_range = temp_range
        self.config = FeramConfig(
            material = material,
            setup    = merge_setups(setup)
        )

    def __iter__(self):
        return (getattr(self, field.name) for field in fields(self))


class ECEConfig:
    # (n_thermalize + n_average) % n_coord_freq must == 0
    def __init__(self, material: Material, common: SetupDict, steps: Mapping[str, Sequence[Setup]]) -> None:
        self.material = material
        self.steps: Mapping[str, FeramConfig] = {
            step: FeramConfig(
                material = material,
                setup = merge_setups(setups) | common
            )
            for step, setups in steps.items()
        }


LOG_SCHEMA: dict[str, pl.DataTypeClass] = {
    'time_step':       pl.Int64,
    'acou_kinetic':    pl.Float64,
    'dipo_kinetic':    pl.Float64,
    'short_range':     pl.Float64,
    'long_range':      pl.Float64,
    'dipole_E_field':  pl.Float64,
    'unharmonic':      pl.Float64,
    'homo_strain':     pl.Float64,
    'homo_coupling':   pl.Float64,
    'inho_strain':     pl.Float64,
    'inho_coupling':   pl.Float64,
    'inho_modulation': pl.Float64,
    'total_energy':    pl.Float64,
    'H_Nose_Poincare': pl.Float64,
    's_Nose':          pl.Float64,
    'pi_Nose':         pl.Float64,
    'u':               pl.List(pl.Float64),
    'u_sigma':         pl.List(pl.Float64),
    'p':               pl.List(pl.Float64),
    'p_sigma':         pl.List(pl.Float64),
}

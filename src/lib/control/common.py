import polars as pl
from pathlib import Path
from typing import NamedTuple
from collections.abc import Mapping

from src.lib.Config import FeramConfig, Material, SetupDict


class Runner(NamedTuple):
    sim_name: str
    working_dir: Path
    feram_path: Path


class TempRange(NamedTuple):
    initial: int
    final: int
    delta: int

class TempConfig(NamedTuple):
    config: FeramConfig
    temperatures: TempRange


class ECEConfig(NamedTuple):
    # (n_thermalize + n_average) % n_coord_freq must == 0
    material: Material
    steps:    Mapping[str, SetupDict]


LOG_SCHEMA = {
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

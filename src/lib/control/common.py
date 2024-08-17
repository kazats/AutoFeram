import polars as pl
from pathlib import Path
from typing import NamedTuple


class Runner(NamedTuple):
    sim_name: str
    working_dir: Path
    feram_path: Path


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

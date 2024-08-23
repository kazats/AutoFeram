import polars as pl
from pathlib import Path
from typing import NamedTuple
from collections.abc import Mapping, Sequence
from itertools import accumulate

from src.lib.common import BoltzmannConst
from src.lib.Config import FeramConfig, Material, Setup, SetupDict, merge_setups


class Runner(NamedTuple):
    sim_name: str
    output_dir: Path
    feram_path: Path


class TempRange(NamedTuple):
    initial: int
    final: int
    delta: int

class TempConfig(NamedTuple):
    material: Material
    temp_range: range
    config: FeramConfig

def temp_config(material: Material, temp_range: TempRange, setup: Sequence[Setup]) -> TempConfig:
    return TempConfig(
        material = material,
        temp_range = range(*temp_range),
        config = FeramConfig(
            material = material,
            setup    = merge_setups(setup)
        )
    )

def post_process_temp(runner: Runner, config: TempConfig) -> pl.DataFrame:
    sim_name, working_dir, _ = runner
    json_name = f'{sim_name}.json'

    df = pl.read_json(working_dir / json_name, schema = LOG_SCHEMA)[1:]
    # df = pl.read_json(working_dir / json_name, schema = LOG_SCHEMA).select(
    #     pl.all(),
    #     *(pl.col(name).list[index].alias(f'{name}_{field}')
    #         for name in ['u', 'u_sigma', 'p', 'p_sigma']
    #         for index, field in enumerate(['x', 'y', 'z'])
    #     )
    # )

    dt   = config.config.setup['dt'] * 1000
    time = accumulate(range(1, len(df)), lambda acc, _: acc + dt, initial=dt)

    return df.with_columns(
        dt_fs   = pl.lit(dt),
        time_fs = pl.Series(time),
        kelvin  = pl.col('dipo_kinetic') / (1.5 * BoltzmannConst)
    )


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

def post_process_ece(runner: Runner, config: ECEConfig) -> pl.DataFrame:
    sim_name, working_dir, _ = runner
    json_name = f'{sim_name}.json'

    def mk_df(step_dir: str, setup: SetupDict) -> pl.DataFrame:
        df = pl.read_json(working_dir / step_dir / json_name, schema = LOG_SCHEMA)[1:]

        return df.with_columns(
            step  = pl.lit(step_dir),
            dt_fs = pl.lit(setup['dt'] * 1000)
        )

    merged_df = pl.concat([mk_df(step_dir, config.setup) for step_dir, config in config.steps.items()])
    time      = pl.Series(accumulate(merged_df['dt_fs'], lambda acc, x: acc + x))
    time_adj  = time - merged_df['dt_fs'][0]  # make time_fs start from 0

    return merged_df.with_columns(
        time_fs = pl.Series(time_adj),
        kelvin  = pl.col('dipo_kinetic') / (1.5 * BoltzmannConst)
    )


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

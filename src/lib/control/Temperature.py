import polars as pl
import colors
from pathlib import Path
from itertools import accumulate
from typing import NamedTuple

from src.lib.common import BoltzmannConst, Vec3
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Log import *
from src.lib.Operations import *
from src.lib.Ovito import WriteOvitoDump
from src.lib.Util import feram_with_fallback, project_root


class TempRunner(NamedTuple):
    sim_name: str
    working_dir: Path
    feram_path: Path


class Temp(NamedTuple):
    initial: int
    final: int
    delta: int


class TempConfig(NamedTuple):
    config: FeramConfig
    temperatures: Temp


def run(runner: TempRunner, temp_config: TempConfig) -> Result[Any, str]:
    sim_name, working_dir, feram_bin = runner
    config, temps = temp_config

    feram_file      = working_dir / f'{sim_name}.feram'
    avg_file        = working_dir / f'{sim_name}.avg'
    thermo_file     = working_dir / 'thermo.avg'
    coord_dir       = working_dir / 'coords'
    dipoRavg_dir    = working_dir / 'dipoRavg'
    dipoRavg_file   = working_dir / f'{sim_name}.dipoRavg'
    last_coord_file = working_dir / f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = working_dir / f'{sim_name}.restart'

    pre = OperationSequence([
        MkDirs(DirOut(working_dir)),
        MkDirs(DirOut(coord_dir)),
        MkDirs(DirOut(dipoRavg_dir)),
        Cd(DirIn(working_dir))
    ])

    def step(temperature: int) -> OperationSequence:
        temp_coord_file    = coord_dir / f'{temperature}.coord'
        temp_dipoRavg_file = dipoRavg_dir / f'{temperature}.dipoRavg'

        config.setup['kelvin'] = temperature

        return OperationSequence([
            Write(FileOut(feram_file),
                  config.generate_feram_file),
            Feram(Exec(feram_bin),
                  FileIn(feram_file)),
            Append(FileIn(avg_file),
                   FileOut(thermo_file)),
            Remove(FileIn(avg_file)),
            Rename(FileIn(dipoRavg_file),
                   FileOut(temp_dipoRavg_file)),
            Copy(FileIn(last_coord_file),
                 FileOut(restart_file)),
            Rename(FileIn(last_coord_file),
                   FileOut(temp_coord_file)),
        ])

    steps = reduce(lambda acc, t: acc + step(t), range(*temps), OperationSequence())

    post = OperationSequence([
        Cd(DirIn(project_root() / 'output')),
        Remove(FileIn(restart_file)),

        WriteOvitoDump(FileOut(working_dir / 'coords.ovito'),
                       DirIn(coord_dir),
                       'coord'),
        WriteOvitoDump(FileOut(working_dir / 'dipoRavgs.ovito'),
                       DirIn(dipoRavg_dir),
                       'dipoRavg'),
        WriteParquet(FileOut(working_dir / f'{working_dir.name}.parquet'),
                     lambda: post_process(runner, temp_config)),
        Archive(DirIn(working_dir),
                FileOut(project_root() / 'output' / f'{working_dir.name}.tar.gz'))
    ])

    all = OperationSequence([
        *pre,
        *steps,
        *post
    ])

    return all.run().and_then(lambda _: Ok('Control Temperature: success'))


def post_process(runner: TempRunner, config: TempConfig) -> pl.DataFrame:
    sim_name, working_dir, _ = runner
    log_name = f'{sim_name}.log'

    log = parse_log(read_log(working_dir / log_name))

    df = pl.DataFrame(log.time_steps,
                      schema_overrides = {
                      'u': pl.List(pl.Float64),
                      'u_sigma': pl.List(pl.Float64),
                      'p': pl.List(pl.Float64),
                      'p_sigma': pl.List(pl.Float64),
                      })

    dt   = config.config.setup['dt'] * 1000
    time = accumulate(range(1, len(df)), lambda acc, _: acc + dt, initial=dt)

    return df.with_columns(
        dt_fs   = pl.lit(dt),
        time_fs = pl.Series(time),
        kelvin  = pl.col('dipo_kinetic') / (1.5 * BoltzmannConst)
    )


if __name__ == "__main__":
    CUSTOM_FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'

    runner = TempRunner(
        sim_name    = 'bto',
        feram_path  = feram_with_fallback(CUSTOM_FERAM_BIN),
        working_dir = project_root() / 'output' / 'temp',
    )

    config = TempConfig(
        FeramConfig(
            setup = merge_setups([
                General(
                    verbose      = 4,
                    L            = Vec3(2, 2, 2),
                    n_thermalize = 1,
                    n_average    = 4,
                    n_coord_freq = 1,
                    bulk_or_film = Structure.Epit
                ),
                EFieldStatic(
                    external_E_field = Vec3(0.001, 0, 0)
                ),
                Strain(
                    epi_strain = Vec3(0.01, 0.01, 0)
                )
            ]),
            material = BTO
        ),
        temperatures = Temp(initial=10, final=20, delta=5)
    )

    res       = run(runner, config)
    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

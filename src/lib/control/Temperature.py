import os
import shutil
import colors
from result import is_err
from pathlib import Path
from typing import cast

from src.lib.common import Vec3, BoltzmannConst

from src.lib import Config
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Operations import *
from src.lib.Log import *
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
    # Ti: int
    # Tf: int
    # dT: int


def run(runner: TempRunner, temp_config: TempConfig) -> Result[Any, str]:

    sim_name, working_dir, feram_bin = runner
    config, temps = temp_config

    feram_file      = working_dir / f'{sim_name}.feram'
    avg_file        = working_dir / f'{sim_name}.avg'
    thermo_file     = working_dir / 'thermo.avg'
    dipoRavg_file   = working_dir / f'{sim_name}.dipoRavg'
    last_coord_file = working_dir / f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = working_dir / f'{sim_name}.restart'

    pre = OperationSequence([
        MkDirs(DirOut(working_dir / 'coords')),
        MkDirs(DirOut(working_dir / 'dipoRavg')),
        Cd(DirIn(working_dir))
    ])

    def step(temperature: int) -> OperationSequence:
        temp_dipoRavg_file = working_dir / 'dipoRavg' / f'{temperature}.dipoRavg'
        temp_coord_file    = working_dir / 'coords' / f'{temperature}.coord'

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
        Remove(FileIn(restart_file))
    ])

    all = OperationSequence([
        *pre,
        *steps,
        *post
    ])

    return all.run().and_then(lambda _: Ok('Control Temperature: success'))


def post_process(log: Log, config: FeramConfig) -> pd.DataFrame:
    dt = config.setup['dt']

    df = pd.DataFrame(log.time_steps)
    df['kelvin'] = df.dipo_kinetic / (1.5 * BoltzmannConst)
    df['time_ps'] = pd.Series(map(lambda x: x * dt, range(len(df))))
    # df['time_ps'] = pd.Series(accumulate(range(df.shape[0]), lambda x, _: x + dt))

    return df


if __name__ == "__main__":
    CUSTOM_FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'


    test_path = project_root() / 'output' / 'temp'
    os.makedirs(test_path, exist_ok=True)

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

    res = run(runner, config)

    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

    # post processing
    log_path = test_path / 'bto.log'
    log_raw  = read_log(log_path)
    log      = parse_log(log_raw)
    res      = post_process(log, config.config)

    print(res)
    # print(len(res))

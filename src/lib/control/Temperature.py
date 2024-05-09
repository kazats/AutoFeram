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
from src.lib.Util import project_root


def run(
    sim_name: str,
    feram_bin: Path,
    dst: Path,
    config: Config.FeramConfig,
    Ti: int,
    Tf: int,
    dT: int
    ) -> Result[Any, str]:

    feram_file      = dst / f'{sim_name}.feram'
    avg_file        = dst / f'{sim_name}.avg'
    thermo_file     = dst / 'thermo.avg'
    dipoRavg_file   = dst / f'{sim_name}.dipoRavg'
    last_coord_file = dst / f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = dst / f'{sim_name}.restart'

    res = OperationSequence([
        MkDirs(DirOut(dst / 'dipoRavg')),
        MkDirs(DirOut(dst / 'coords'))
    ]).run()

    if is_err(res):
        return res

    for temperature in range(Ti, Tf, dT):
        temp_dipoRavg_file = dst / 'dipoRavg' / f'{temperature}.dipoRavg'
        temp_coord_file    = dst / 'coords' / f'{temperature}.coord'

        config.setup['kelvin'] = temperature

        res = OperationSequence([
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
        ]).run()

        if is_err(res):
            return res

    Remove(FileIn(restart_file)).run()

    return Ok('Control Temperature: success')


def post_process(log: Log, config: FeramConfig) -> pd.DataFrame:
    dt = config.setup['dt']

    df = pd.DataFrame(log.timesteps)
    df['kelvin'] = df.dipo_kinetic / (1.5 * BoltzmannConst)
    df['time_ps'] = pd.Series(map(lambda x: x * dt, range(len(df))))
    # df['time_ps'] = pd.Series(accumulate(range(df.shape[0]), lambda x, _: x + dt))

    return df


if __name__ == "__main__":
    SIM_NAME = 'bto'
    # FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'   # FERAM_BIN = Path('feram')
    FERAM_BIN = Path(cast(str, shutil.which('feram')))


    test_path = project_root() / 'output' / 'temp'
    os.makedirs(test_path, exist_ok=True)

    config = FeramConfig(
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
    )

    res = run(SIM_NAME, FERAM_BIN,
              test_path, config,
              Ti=10, Tf=20, dT=5)

    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

    # post processing
    log_path  = test_path / 'bto.log'
    log_raw   = read_log(log_path)
    log       = parse_log(log_raw)
    res       = post_process(log, config)

    print(res)
    # print(len(res))

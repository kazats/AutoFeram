import os
import shutil
import colors
from result import is_err
from pathlib import Path
from dataclasses import dataclass
from itertools import zip_longest
from typing import NamedTuple, cast

from src.lib.common import BoltzmannConst, Vec3
from src.lib.control import ECE
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Util import project_root
from src.lib.Log import *
from src.lib.Operations import *


class ECERunner(NamedTuple):
    sim_name: str
    feram_bin: Path
    working_dir: Path


@dataclass
class ECEConfig:
    material:      Material
    common:        SetupDict
    step1_preNPT:  list[Setup]
    step2_preNPE:  list[Setup]
    step3_rampNPE: list[Setup]
    step4_postNPE: list[Setup]


def run(
    runner: ECERunner,
    ece_config: ECEConfig
    ):
    sim_name, feram_bin, working_dir = runner

    def setup_with(setups: list[Setup]) -> FeramConfig:
        return FeramConfig(
            setup    = merge_setups(setups) | ece_config.common,
            material = ece_config.material
        )

    steps = [
        (working_dir / '1_preNPT',  ece_config.step1_preNPT),
        (working_dir / '2_preNPE',  ece_config.step2_preNPE),
        (working_dir / '3_rampNPE', ece_config.step3_rampNPE),
        (working_dir / '4_postNPE', ece_config.step4_postNPE)
    ]

    res = OperationSequence([MkDirs(DirOut(dir))
        for dir, _ in steps]).run()

    if is_err(res):
        return res


    for (dir, setups), (dir_next, _) in zip_longest(steps, steps[1:], fillvalue=(Any, Any)):
        config          = setup_with(setups)
        feram_file      = dir / f'{sim_name}.feram'
        last_coord_file = dir / f'{sim_name}.{config.last_coord()}.coord'
        maybe_copy      = Copy(FileIn(last_coord_file),
                               FileOut(dir_next / f'{sim_name}.restart'))\
                            if dir_next is not Any else Empty()

        res = OperationSequence([
            Write(FileOut(feram_file),
                  config.generate_feram_file),
            WithDir(DirIn(working_dir),
                    DirIn(dir),
                    Feram(Exec(feram_bin),
                          FileIn(feram_file))),
            maybe_copy
        ]).run()

        if is_err(res):
            return res

    return Ok('Measure ECE: success')


def post_process(log: Log, config: ECEConfig) -> pd.DataFrame:
    dt = config.step1_preNPT[0].to_dict()['dt']

    df = pd.DataFrame(log.timesteps)
    df['kelvin'] = df.dipo_kinetic / (1.5 * BoltzmannConst)
    df['time_ps'] = pd.Series(map(lambda x: x * dt, range(len(df))))
    # df['time_ps'] = pd.Series(accumulate(range(df.shape[0]), lambda x, _: x + dt))

    return df


if __name__ == "__main__":
    SIM_NAME = 'bto'
    # FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'   # FERAM_BIN = Path('feram')
    FERAM_BIN = Path(cast(str, shutil.which('feram')))


    working_dir = project_root() / 'output' / 'ece'
    os.makedirs(working_dir, exist_ok=True)

    material       = BTO
    temperature    = 200
    size           = Vec3(2, 2, 2)
    efield_initial = Vec3(0.001, 0, 0)
    efield_final   = Vec3[float](0, 0, 0)
    efield_static  = EFieldStatic(external_E_field = efield_initial)

    config = ECE.ECEConfig(
        material = material,
        common = {
            'L':      size,
            'kelvin': temperature,
        },
        step1_preNPT = [
            General(
                method       = Method.MD,
                n_thermalize = 0,
                n_average    = 8, #0000
                n_coord_freq = 8, #0000
            ),
            efield_static
        ],
        step2_preNPE = [
            General(
                method       = Method.LF,
                n_thermalize = 0,
                n_average    = 12, #0000
                n_coord_freq = 12, #0000
            ),
            efield_static
        ],
        step3_rampNPE = [
            General(
                method       = Method.LF,
                n_thermalize = 10, #0000
                n_average    = 0,
                n_coord_freq = 10, #0000
            ),
            EFieldDynamic(
                n_hl_freq        = 1, #00
                n_E_wave_period  = 4, #100000,
                E_wave_type      = EWaveType.RampOff,
                external_E_field = efield_initial
            )
        ],
        step4_postNPE = [
            General(
                method       = Method.LF,
                n_thermalize = 0,
                n_average    = 18, #0000
                n_coord_freq = 18, #0000
            ),
            efield_static
        ]
    )

    runner = ECERunner(
        sim_name    = SIM_NAME,
        feram_bin   = FERAM_BIN,
        working_dir = working_dir,
    )

    res = run(
        runner,
        config
    )

    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

    # post processing
    # log_path  = out_path / 'bto.log'
    # log_raw   = read_log(log_path)
    # log       = parse_log(log_raw)
    # res       = post_process(log, config)

    # print(res)
    # print(len(res))

import colors
from pathlib import Path
from functools import reduce
from itertools import zip_longest
from typing import NamedTuple

from src.lib.common import BoltzmannConst, Vec3
from src.lib.control import ECE
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Util import feram_path, project_root
from src.lib.Log import *
from src.lib.Operations import *


class ECERunner(NamedTuple):
    sim_name: str
    feram_bin: Path
    working_dir: Path

class ECEConfig(NamedTuple):
    material: Material
    common:   SetupDict
    steps:    dict[str, list[Setup]]


def run(runner: ECERunner, ece_config: ECEConfig) -> Result[Any, str]:

    def setup_with(setups: list[Setup]) -> FeramConfig:
        return FeramConfig(
            setup    = merge_setups(setups) | ece_config.common,
            material = ece_config.material
        )

    sim_name, feram_bin, working_dir = runner

    create_dirs = OperationSequence([
        MkDirs(DirOut(working_dir)),
        *[MkDirs(DirOut(working_dir / step_dir)) for step_dir in ece_config.steps.keys()]
    ])

    def step(setups: list[Setup], dir_cur: Path, dir_next: Path) -> OperationSequence:
        config          = setup_with(setups)
        feram_file      = dir_cur / f'{sim_name}.feram'
        last_coord_file = dir_cur / f'{sim_name}.{config.last_coord()}.coord'
        copy_restart    = Copy(FileIn(last_coord_file),
                               FileOut(dir_next / f'{sim_name}.restart')) if dir_next is not Any else Empty()

        return OperationSequence([
            Write(FileOut(feram_file),
                  config.generate_feram_file),
            WithDir(DirIn(working_dir),
                    DirIn(dir_cur),
                    Feram(Exec(feram_bin),
                          FileIn(feram_file))),
            copy_restart
        ])

    def reducer(acc: OperationSequence, next_step) -> OperationSequence:
        (dir_cur, setups), (dir_next, _) = next_step
        return acc + step(setups, dir_cur, dir_next)

    steps     = [(working_dir / step_dir, setups) for step_dir, setups in ece_config.steps.items()]
    step_zip  = zip_longest(steps, steps[1:], fillvalue=(Any, Any))
    run_steps = reduce(reducer, step_zip, OperationSequence())

    all = OperationSequence([
        *create_dirs,
        *run_steps
    ])

    return all.run().and_then(lambda _: Ok('Measure ECE: success'))


def post_process(runner: ECERunner, config: ECEConfig) -> pd.DataFrame:
    sim_name, feram_bin, working_dir = runner
    dt = config.step1_preNPT[0].to_dict()['dt']

    df = pd.DataFrame(log.timesteps)
    df['kelvin'] = df.dipo_kinetic / (1.5 * BoltzmannConst)
    df['time_ps'] = pd.Series(map(lambda x: x * dt, range(len(df))))
    # df['time_ps'] = pd.Series(accumulate(range(df.shape[0]), lambda x, _: x + dt))

    return df


if __name__ == "__main__":
    CUSTOM_FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'

    material       = BTO
    temperature    = 200
    size           = Vec3(2, 2, 2)
    efield_initial = Vec3(0.001, 0, 0)
    efield_final   = Vec3[float](0, 0, 0)
    efield_static  = EFieldStatic(external_E_field = efield_initial)

    runner = ECERunner(
        sim_name    = 'bto',
        feram_bin   = feram_path(CUSTOM_FERAM_BIN),
        working_dir = project_root() / 'output' / 'ece',
    )

    config = ECE.ECEConfig(
        material = material,
        common = {
            'L':      size,
            'kelvin': temperature,
        },
        steps = {
            '1_preNPT': [
                General(
                    method       = Method.MD,
                    n_thermalize = 0,
                    n_average    = 8, #0000
                    n_coord_freq = 8, #0000
                ),
                efield_static
            ],
            '2_preNPE': [
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 12, #0000
                    n_coord_freq = 12, #0000
                ),
                efield_static
            ],
            '3_rampNPE': [
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
            '4_postNPE': [
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 18, #0000
                    n_coord_freq = 18, #0000
                ),
                efield_static
            ]
        })

    res = run(runner, config)

    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

    # post processing
    # log_path  = out_path / 'bto.log'
    # log_raw   = read_log(log_path)
    # log       = parse_log(log_raw)
    # res       = post_process(log, config)

    # print(res)
    # print(len(res))

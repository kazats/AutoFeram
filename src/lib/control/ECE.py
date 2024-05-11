import colors
from pathlib import Path
from functools import reduce
from itertools import accumulate, zip_longest
from typing import NamedTuple

from src.lib.common import BoltzmannConst, Vec3
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Util import feram_path, project_root
from src.lib.Log import *
from src.lib.Operations import *


class ECERunner(NamedTuple):
    sim_name: str
    working_dir: Path
    feram_path: Path

class ECEConfig(NamedTuple):
    material: Material
    steps:    dict[str, SetupDict]


def run(runner: ECERunner, ece_config: ECEConfig) -> Result[Any, str]:

    def setup_with(setup: SetupDict) -> FeramConfig:
        return FeramConfig(
            setup    = setup,
            material = ece_config.material
        )

    sim_name, working_dir, feram_bin = runner

    create_dirs = OperationSequence([
        MkDirs(DirOut(working_dir)),
        *[MkDirs(DirOut(working_dir / step_dir)) for step_dir in ece_config.steps.keys()]
    ])

    def step(setup: SetupDict, dir_cur: Path, dir_next: Path) -> OperationSequence:
        config          = setup_with(setup)
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
    sim_name, working_dir, _ = runner
    log_name = f'{sim_name}.log'

    def mk_df(step_dir: str, setup: SetupDict) -> pd.DataFrame:
        log = parse_log(read_log(working_dir / step_dir / log_name))
        df  = pd.DataFrame(log.time_steps)

        df['dt_e3'] = setup['dt'] * 1000

        return df

    dfs = [mk_df(step_dir, setup) for step_dir, setup in config.steps.items()]

    merged_df = pd.concat(dfs, ignore_index=True)
    time      = accumulate(merged_df['dt_e3'],
                           lambda acc, x: acc + x,
                           initial=0)

    merged_df['time_fs'] = pd.Series(time)
    merged_df['kelvin']  = merged_df.dipo_kinetic / (1.5 * BoltzmannConst)

    return merged_df


if __name__ == "__main__":
    pd.options.mode.copy_on_write = True

    CUSTOM_FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'

    material       = BTO
    size           = Vec3(2, 2, 2)
    temperature    = 200
    efield_initial = Vec3(0.001, 0, 0)
    efield_final   = Vec3[float](0, 0, 0)
    efield_static  = EFieldStatic(external_E_field = efield_initial)

    common = {
        'L':      size,
        'kelvin': temperature,
    }

    runner = ECERunner(
        sim_name    = 'bto',
        feram_path  = feram_path(CUSTOM_FERAM_BIN),
        working_dir = project_root() / 'output' / 'ece',
    )

    config = ECEConfig(
        material = material,
        steps = {
            '1_preNPT': merge_setups([
                General(
                    method       = Method.MD,
                    n_thermalize = 0,
                    n_average    = 8, #0000
                    n_coord_freq = 8, #0000
                ),
                efield_static
            ]) | common,
            '2_preNPE': merge_setups([
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 12, #0000
                    n_coord_freq = 12, #0000
                ),
                efield_static
            ]) | common,
            '3_rampNPE': merge_setups([
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
            ]) | common,
            '4_postNPE': merge_setups([
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 18, #0000
                    n_coord_freq = 18, #0000
                ),
                efield_static
            ]) | common
        })

    res = run(runner, config)

    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

    # post processing
    res = post_process(runner, config)

    write_path = runner.working_dir / 'ece.pickle'
    res.to_pickle(write_path)

    print(res)

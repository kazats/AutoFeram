import polars as pl
from pathlib import Path
from functools import reduce
from itertools import accumulate, zip_longest

from src.lib.common import *
from src.lib.control.common import *
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Domain import *
from src.lib.Log import *
from src.lib.Operations import *
from src.lib.Ovito import WriteOvitoDump
from src.lib.Util import *


def run(runner: Runner, ece_config: ECEConfig) -> Result[Any, str]:

    def setup_with(setup: SetupDict) -> FeramConfig:
        return FeramConfig(
            material = ece_config.material,
            setup    = setup
        )

    sim_name, working_dir, feram_bin = runner

    pre = OperationSequence([
        MkDirs(DirOut(working_dir, preconditions=[dir_doesnt_exist])),
        *[MkDirs(DirOut(working_dir / step_dir)) for step_dir in ece_config.steps.keys()]
    ])

    def step(setup: SetupDict, dir_cur: Path, dir_next: Path) -> OperationSequence:
        config          = setup_with(setup)
        feram_file      = dir_cur / f'{sim_name}.feram'
        last_coord_file = dir_cur / f'{sim_name}.{config.last_coord()}.coord'
        copy_restart    = Copy(FileIn(last_coord_file),
                               FileOut(dir_next / f'{sim_name}.restart')) if dir_next is not Any else Empty()

        return OperationSequence([
            Write(FileOut(feram_file), config.generate_feram_file),
            WithDir(DirIn(working_dir), DirIn(dir_cur),
                    Feram(Exec(feram_bin), FileIn(feram_file))),
            copy_restart,
            WriteOvitoDump(FileOut(working_dir / f'coords_{dir_cur.name}.ovt'), DirIn(dir_cur), 'coord'),
            WriteOvitoDump(FileOut(working_dir / f'dipoRavgs_{dir_cur.name}.ovt'), DirIn(dir_cur), 'dipoRavg')
        ])

    def reducer(acc: OperationSequence, next_step) -> OperationSequence:
        (dir_cur, setups), (dir_next, _) = next_step
        return acc + step(setups, dir_cur, dir_next)

    steps     = [(working_dir / step_dir, setups) for step_dir, setups in ece_config.steps.items()]
    step_zip  = zip_longest(steps, steps[1:], fillvalue=(Any, Any))
    steps_all = reduce(reducer, step_zip, OperationSequence())

    post = OperationSequence([
        Copy(FileIn(Path(__file__)), FileOut(working_dir / 'AutoFeram_control.py')),
        WriteParquet(FileOut(working_dir / f'{working_dir.name}.parquet'), lambda: post_process(runner, ece_config)),
        Archive(DirIn(working_dir), FileOut(project_root() / 'output' / f'{working_dir.name}.tar.gz'))
    ])

    all = OperationSequence([
        pre,
        steps_all,
        post
    ])

    return all.run().and_then(
        lambda _: Ok('ECE: Success')).map_err(
        lambda _: 'ECE: Failure')


def post_process(runner: Runner, config: ECEConfig) -> pl.DataFrame:
    sim_name, working_dir, _ = runner
    log_name = f'{sim_name}.log'

    def mk_df(step_dir: str, setup: SetupDict) -> pl.DataFrame:
        log = parse_log(read_log(working_dir / step_dir / log_name))
        df  = pl.DataFrame(log.time_steps,
                           schema_overrides = {
                           'u':       pl.List(pl.Float64),
                           'u_sigma': pl.List(pl.Float64),
                           'p':       pl.List(pl.Float64),
                           'p_sigma': pl.List(pl.Float64),
                           })

        return df.with_columns(
            step  = pl.lit(step_dir),
            dt_fs = pl.lit(setup['dt'] * 1000)
        )

    merged_df = pl.concat([mk_df(step_dir, setup) for step_dir, setup in config.steps.items()])
    time      = accumulate(merged_df['dt_fs'], lambda acc, x: acc + x)

    return merged_df.with_columns(
        time_fs = pl.Series(time),
        kelvin  = pl.col('dipo_kinetic') / (1.5 * BoltzmannConst)
    )


if __name__ == "__main__":
    CUSTOM_FERAM_BIN = Path.home() / 'feram_dev/build/src/feram'

    runner = Runner(
        sim_name    = 'bto',
        feram_path  = CUSTOM_FERAM_BIN,
        working_dir = project_root() / 'output' / f'ece_{timestamp()}',
    )

    efield_initial = Vec3(0.001, 0, 0)
    efield_final   = Vec3[float](0, 0, 0)
    efield_static  = EFieldStatic(external_E_field = efield_initial)

    common = {
        'L':      Int3(2, 2, 2),
        'kelvin': 200,
    }

    config = ECEConfig(
        material = BTO,
        steps = {
            '1_preNPT': merge_setups([
                General(
                    method       = Method.MD,
                    n_thermalize = 0,
                    n_average    = 8, #0000
                    n_coord_freq = 2, #0000
                ),
                efield_static
            ]) | common,
            '2_preNPE': merge_setups([
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 12, #0000
                    n_coord_freq = 2, #0000
                ),
                efield_static
            ]) | common,
            '3_rampNPE': merge_setups([
                General(
                    method       = Method.LF,
                    n_thermalize = 10, #0000
                    n_average    = 0,
                    n_coord_freq = 2, #0000
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
                    n_coord_freq = 2, #0000
                ),
                efield_static
            ]) | common
        })

    print(colorize(run(runner, config)))

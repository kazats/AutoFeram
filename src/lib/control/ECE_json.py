from pathlib import Path
from itertools import zip_longest

from src.lib.common import *
from src.lib.control.common import *
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Domain import *
from src.lib.Operations import *
from src.lib.Ovito import WriteOvito
from src.lib.Util import *


def run(runner: Runner, ece_config: ECEConfig) -> OperationR:
    sim_name, working_dir, feram_bin = runner
    src_file                         = Path(__file__)

    pre = OperationSequence([
        # MkDirs(DirOut(working_dir, preconditions=[dir_doesnt_exist])),
        MkDirs(DirOut(working_dir)),
        *[MkDirs(DirOut(working_dir / step_dir)) for step_dir in ece_config.steps.keys()]
    ])

    def step(config: FeramConfig | Any, dir_cur: Path | Any, dir_next: Path | Any) -> OperationSequence:
        feram_file      = dir_cur / f'{sim_name}.feram'
        last_coord_file = dir_cur / f'{sim_name}.{config.last_coord()}.coord'
        copy_restart    = Copy(FileIn(last_coord_file),
                               FileOut(dir_next / f'{sim_name}.restart')) if dir_next is not Any else Empty()

        return OperationSequence([
            Write(FileOut(feram_file), config.generate_feram_file),
            WithDir(DirIn(working_dir), DirIn(dir_cur),
                    Feram(Exec(feram_bin), FileIn(feram_file))),
            copy_restart,
            WriteOvito(FileOut(working_dir / f'coords_{dir_cur.name}.ovt'), DirIn(dir_cur), 'coord'),
            WriteOvito(FileOut(working_dir / f'dipoRavgs_{dir_cur.name}.ovt'), DirIn(dir_cur), 'dipoRavg')
        ])

    steps     = [(working_dir / step_dir, setup) for step_dir, setup in ece_config.steps.items()]
    step_zip  = zip_longest(steps, steps[1:], fillvalue=(Any, Any))
    steps_all = OperationSequence(
        step(setup, dir_cur, dir_next)
        for (dir_cur, setup), (dir_next, _) in step_zip
    )

    post = OperationSequence([
        Copy(FileIn(src_file), FileOut(working_dir / f'AutoFeram_{src_file.name}')),
        WriteParquet(FileOut(working_dir / f'{working_dir.name}.parquet'), lambda: post_process_ece(runner, ece_config)),
        Archive(DirIn(working_dir), FileOut(project_root() / 'output' / f'{working_dir.name}.tar.gz'))
    ])

    return OperationSequence([
        pre,
        steps_all,
        post,
        Success(src_file.name)
    ]).run()


if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bto',
        feram_path  = feram_with_fallback(Path.home() / 'feram_dev/build/src/feram'),
        working_dir = project_root() / 'output' / f'ece_json_{timestamp()}',
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
        common = common,
        steps = {
            '1_preNPT': [
                General(
                    method       = Method.MD,
                    n_thermalize = 0,
                    n_average    = 8, #0000
                    n_coord_freq = 2, #0000
                ),
                efield_static
            ],
            '2_preNPE': [
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 12, #0000
                    n_coord_freq = 2, #0000
                ),
                efield_static
            ],
            '3_rampNPE': [
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
            ],
            '4_postNPE': [
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 18, #0000
                    n_coord_freq = 2, #0000
                ),
                efield_static
            ]
        })

    run(runner, config)

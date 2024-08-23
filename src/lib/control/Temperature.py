from copy import deepcopy
from pathlib import Path

from src.lib.common import *
from src.lib.control.common import *
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Log import *
from src.lib.Operations import *
from src.lib.Ovito import WriteOvito
from src.lib.Util import *


def run(runner: Runner, temp_config: TempConfig) -> OperationR:
    sim_name, working_dir, feram_bin = runner
    _, temps, config                 = temp_config
    src_file                         = Path(__file__)

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

        step_config = deepcopy(config)
        step_config.setup['kelvin'] = temperature

        return OperationSequence([
            Write(FileOut(feram_file), step_config.generate_feram_file),
            Feram(Exec(feram_bin), FileIn(feram_file)),
            Append(FileIn(avg_file), FileOut(thermo_file)),
            Remove(FileIn(avg_file)),
            Rename(FileIn(dipoRavg_file), FileOut(temp_dipoRavg_file)),
            Copy(FileIn(last_coord_file), FileOut(restart_file)),
            Rename(FileIn(last_coord_file), FileOut(temp_coord_file)),
        ])

    steps = OperationSequence(map(step, temps))

    post = OperationSequence([
        Copy(FileIn(src_file), FileOut(working_dir / f'AutoFeram_{src_file.name}')),
        Remove(FileIn(restart_file)),
        WriteOvito(FileOut(working_dir / 'coords.ovt'), DirIn(coord_dir), 'coord'),
        WriteOvito(FileOut(working_dir / 'dipoRavgs.ovt'), DirIn(dipoRavg_dir), 'dipoRavg'),
        WriteParquet(FileOut(working_dir / f'{working_dir.name}.parquet'), lambda: post_process_temp(runner, temp_config)),
        Archive(DirIn(working_dir), FileOut(project_root() / 'output' / f'{working_dir.name}.tar.gz'))
    ])

    return OperationSequence([
        pre,
        steps,
        post,
        Success(src_file.name)
    ]).run()


if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bto',
        feram_path  = feram_with_fallback(Path.home() / 'feram_dev/build/src/feram'),
        working_dir = project_root() / 'output' / f'temperature_{timestamp()}',
    )

    config = temp_config(
        material = BTO,
        temp_range = TempRange(initial = 350, final = 340, delta = -5),
        setup = [
            General(
                L            = Int3(2, 2, 2),
                n_thermalize = 4,
                n_average    = 2,
                n_coord_freq = 6,
                bulk_or_film = Structure.Bulk
            ),
            # EFieldStatic(
            #     external_E_field = Vec3(0.001, 0, 0)
            # ),
            # Strain(
            #     epi_strain = Vec3(0.01, 0.01, 0)
            # )
        ]

    )

    run(runner, config)

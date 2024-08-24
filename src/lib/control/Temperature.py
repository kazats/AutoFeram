from copy import deepcopy
from pathlib import Path

from src.lib.common import *
from src.lib.control.common import *
from src.lib.Config import *
from src.lib.Log import *
from src.lib.Materials import BTO
from src.lib.Operations import *
from src.lib.Ovito import WriteOvito
from src.lib.Util import *


def run(runner: Runner, temp_config: TempConfig, add_pre: Operation = Empty()) -> OperationR:
    sim_name, output_dir, feram_bin = runner
    _, temps, config                = temp_config

    src_file        = caller_src_path()
    feram_file      = output_dir / f'{sim_name}.feram'
    avg_file        = output_dir / f'{sim_name}.avg'
    thermo_file     = output_dir / 'thermo.avg'
    coord_dir       = output_dir / 'coords'
    dipoRavg_dir    = output_dir / 'dipoRavg'
    dipoRavg_file   = output_dir / f'{sim_name}.dipoRavg'
    last_coord_file = output_dir / f'{sim_name}.{config.last_coord}.coord'
    restart_file    = output_dir / f'{sim_name}.restart'

    artifacts_dir   = output_dir / '_artifacts'
    ovito_dir       = artifacts_dir / 'ovito'
    af_src_file     = artifacts_dir / f'AutoFeram_{src_file.name}'
    parquet_file    = artifacts_dir / f'{sim_name}.parquet'

    pre = OperationSequence([
        Message('Pre'),
        MkDirs(DirOut(output_dir)),
        MkDirs(DirOut(coord_dir)),
        MkDirs(DirOut(dipoRavg_dir)),
        Cd(DirIn(output_dir)),
        add_pre
    ])

    def step(temperature: int) -> OperationSequence:
        temp_coord_file    = coord_dir / f'{temperature}.coord'
        temp_dipoRavg_file = dipoRavg_dir / f'{temperature}.dipoRavg'

        step_config = deepcopy(config)
        step_config.setup['kelvin'] = temperature

        return OperationSequence([
            Message(f'Temperature: {temperature}'),
            Write(FileOut(feram_file), step_config.generate_feram_file),
            Feram(Exec(feram_bin), FileIn(feram_file)),
            Append(FileIn(avg_file), FileOut(thermo_file)),
            Remove(FileIn(avg_file)),
            Rename(FileIn(dipoRavg_file), FileOut(temp_dipoRavg_file)),
            Copy(FileIn(last_coord_file), FileOut(restart_file)),
            Rename(FileIn(last_coord_file), FileOut(temp_coord_file)),
        ])

    main = OperationSequence(map(step, temps))

    post = OperationSequence([
        Message('Post'),
        Remove(FileIn(restart_file)),

        MkDirs(DirOut(artifacts_dir)),
        Copy(FileIn(src_file), FileOut(af_src_file)),

        MkDirs(DirOut(ovito_dir)),
        WriteOvito(DirIn(coord_dir), FileOut(ovito_dir / 'coords.ovt'), 'coord'),
        WriteOvito(DirIn(dipoRavg_dir), FileOut(ovito_dir / 'dipoRavgs.ovt'), 'dipoRavg'),

        WriteParquet(FileOut(parquet_file), lambda: post_process_temp(runner, temp_config)),
        Archive(DirIn(output_dir), FileOut(project_root() / 'output' / f'{output_dir.name}.tar.gz'))
    ])

    return OperationSequence([
        pre,
        Message('Main'),
        main,
        post,
        Success(src_file.name)
        # Success(working_dir.name)
    ]).run()


if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bto',
        feram_path  = feram_with_fallback(Path.home() / 'feram_dev/build/src/feram'),
        output_dir  = project_root() / 'output' / f'temperature_{timestamp()}',
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

from pathlib import Path

from src.lib.common import Int3, Vec3
from src.lib.control import Temperature
from src.lib.control.common import Runner, TempRange, temp_config
from src.lib.Config import General, Structure, Strain
from src.lib.Domain import ModulationWriter, generate_coords
from src.lib.Materials import BTO
from src.lib.Util import exit_from_result, feram_with_fallback, project_root, timestamp

import os
import sys
sys.path.append('/home/lt/Code/git/fedas/src/')
from generate_defects import Defects


if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bst',
        feram_path  = feram_with_fallback(Path.home() / 'Code/git/feram-0.26.04_dev/build/src/feram'),
        output_dir  = project_root() / 'output' / f'defect_temp_{timestamp()}'
    )

    config = temp_config(
        material = BTO,
        temp_range = TempRange(initial = 600, final = 595, delta = -5),
        setup = [
            General(
                L            = Int3(8, 8, 8),
                n_thermalize = 8,
                n_average    = 2,
                n_coord_freq = 10,
                bulk_or_film = Structure.Epit
            ),
            # EFieldStatic(
            #     external_E_field = Vec3(0.001, 0, 0)
            # ),
            # Strain(
            #    epi_strain = Vec3(0.006, 0.006, 0)
            # )
        ]
    )


    fname = 'new.defects'
    size=(8,8,8)
    D=Defects(size=size)
    df_dist = dict(mux=0.01, sigmax=0.00)
    rnd = D.random_df(mode='normal', percent=1, seed=0, xlim=None, ylim=None, zlim=None, **df_dist)
    defects_all = [rnd]
    with open(runner.output_dir/fname, 'w') as fw:
        for _df in defects_all:
            fw.writelines(_df)
    os.system('more %s'%fname)


    exit_from_result(Temperature.run(runner, config))

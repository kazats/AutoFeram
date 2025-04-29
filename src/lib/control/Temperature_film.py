from copy import deepcopy
from pathlib import Path

from src.lib.common import *
from src.lib.control import Temperature
from src.lib.control.common import *
from src.lib.Config import *
from src.lib.Materials import BTO
from src.lib.Operations import *
from src.lib.Ovito import WriteOvito
from src.lib.Util import *



if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bto',
        feram_path  = feram_with_fallback(Path.home() / 'Code/git/feram-0.26.04_dev/build/src/feram'),
        output_dir  = project_root() / 'output' / f'temperature_{timestamp()}',
    )

    config = temp_config(
        material = BTO,
        temp_range = TempRange(initial = 350, final = 340, delta = -5),
        setup = [
            General(
                L            = Int3(2, 2, 4),
                n_thermalize = 4,
                n_average    = 2,
                n_coord_freq = 6,
                bulk_or_film = Structure.Epit_001
            ),
            # EFieldStatic(
            #     external_E_field = Vec3(0.001, 0, 0)
            # ),
            Film(
                gap_id = 2,
            ),
            Strain(
                epi_strain = Vec3(0.01, 0.01, 0),
            )
        ]
    )

    exit_from_result(Temperature.run(runner, config))

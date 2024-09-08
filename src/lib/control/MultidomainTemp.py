from pathlib import Path

from src.lib.common import Int3
from src.lib.control import Temperature
from src.lib.control.common import Runner, TempRange, temp_config
from src.lib.Config import General, Structure
from src.lib.Domain import Domain, LocalfieldWriter, Props
from src.lib.Materials import BTO
from src.lib.Util import exit_from_result, feram_with_fallback, project_root, timestamp


if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bto',
        feram_path  = feram_with_fallback(Path.home() / 'Code/git/feram-0.26.04_dev/build/src/feram'),
        output_dir  = project_root() / 'output' / f'multidomain_temp_{timestamp()}'
    )

    config = temp_config(
        material = BTO,
        temp_range = TempRange(initial = 350, final = 340, delta = -5),
        setup = [
            General(
                L            = Int3(3, 3, 3),
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

    lf_writer = LocalfieldWriter(
        output_path = runner.output_dir / f'{runner.sim_name}.localfield',
        size = config.config.setup['L'],
        domains = [Domain(Int3(0, 0, 0), Props(0, 0, 0)),
                   Domain(Int3(1, 0, 0), Props(0, 1, 0)),
                   # Domain(Int3(12, 47, 0), Props(1, 0, 0)),
                   # Domain(Int3(24, 24, 0), Props(0, -1, 0)),
                   ]
    )

    exit_from_result(Temperature.run(runner, config, add_pre = lf_writer))

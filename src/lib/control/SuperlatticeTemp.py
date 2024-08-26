from pathlib import Path

from src.lib.common import Int3
from src.lib.control import Temperature
from src.lib.control.common import Runner, TempRange, temp_config
from src.lib.Config import General, Structure
from src.lib.Domain import ModulationWriter, generate_coords
from src.lib.Materials import BST
from src.lib.Util import feram_with_fallback, project_root, timestamp


if __name__ == "__main__":
    runner = Runner(
        sim_name   = 'bst',
        feram_path = feram_with_fallback(Path.home() / 'Code/git/feram-0.26.04_dev/build/src/feram'),
        output_dir = project_root() / 'output' / f'superlattice_temp_{timestamp()}'
    )

    config = temp_config(
        material = BST,
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

    mod_writer = ModulationWriter(
        output_path = runner.output_dir / f'{runner.sim_name}.modulation',
        coords = generate_coords(config.config.setup['L']),
        bto_sto = (1, 1)  # sum(bto_sto) should == size.z
    )

    Temperature.run(runner, config, add_pre = mod_writer)

from pathlib import Path

from src.lib.common import Int3, Vec3
from src.lib.control import Temperature
from src.lib.control.common import Runner, TempRange, temp_config
from src.lib.Config import General, Structure, Strain
from src.lib.Domain import ModulationWriter, generate_coords
from src.lib.Materials import BST
from src.lib.Util import feram_with_fallback, project_root, timestamp


if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bst',
        feram_path  = Path.home() / 'feram_dev/build/src/feram',
        output_dir  = project_root() / 'output' / f'superlattice_temp_{timestamp()}'
    )

    config = temp_config(
        material = BST,
        temp_range = TempRange(initial = 600, final = 100, delta = -5),
        setup = [
            General(
                L            = Int3(96, 96, 12),
                n_thermalize = 80000,
                n_average    = 20000,
                n_coord_freq = 100000,
                bulk_or_film = Structure.Epit
            ),
            # EFieldStatic(
            #     external_E_field = Vec3(0.001, 0, 0)
            # ),
            Strain(
               epi_strain = Vec3(0.006, 0.006, 0)
            )
        ]
    )

    mod_writer = ModulationWriter(
        output_path = runner.output_dir / f'{runner.sim_name}.modulation',
        coords = generate_coords(config.config.setup['L']),
        bto_sto = (6, 6)  # sum(bto_sto) should == size.z
    )

    Temperature.run(runner, config, add_pre = mod_writer)

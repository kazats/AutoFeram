import os
import shutil
from pathlib import Path
from typing import cast

from src.lib import Config
from src.lib.control import Temperature, ECE
from src.lib.materials.BTO import BTO
from src.lib.Util import src_root


if __name__ == "__main__":
    test_path = src_root()/'test'/'temp'
    os.makedirs(test_path, exist_ok=True)


    SIM_NAME = 'bto'
    # FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'   # FERAM_BIN = Path('feram')
    FERAM_BIN = Path(cast(str, shutil.which('feram')))


    config = Config.FeramConfig(
        setup = Config.merge_setups([
            Config.General(
                verbose      = 1,
                L            = '2 2 2',
                n_thermalize = 1,
                n_average    = 4,
                n_coord_freq = 1,
                bulk_or_film = 'epit'
            ),
            Config.EFieldStatic(
                external_E_field = '0.001 0 0'
            ),
            Config.Strain(
                epi_strain = '0.01 0.01 0'
            )
        ]),
        material = BTO
    )
    Temperature.control_temperature(config, SIM_NAME, FERAM_BIN, test_path, Ti=10, Tf=20, dT=5)


    # material       = BTO
    # temperature    = 200
    # efield_initial = '0.001 0 0'
    # efield_final   = '0 0 0'
    # # params = { 'kelvin': temperature, 'L': '1 1 1' }
    #
    # Control.measure_ece(
    #     SIM_NAME,
    #     FERAM_BIN,
    #     Control.ECEConfig(
    #         material = material,
    #         step1_preNPT = [
    #             Config.General(
    #                 n_thermalize = 0,
    #                 n_average    = 8, #0000
    #                 n_coord_freq = 8, #0000
    #             ),
    #             Config.EFieldStatic(
    #                 external_E_field = efield_initial
    #             )
    #         ],
    #         step2_preNPE = [
    #             Config.General(
    #                 method       = 'lf',
    #                 n_thermalize = 0,
    #                 n_average    = 12, #0000
    #                 n_coord_freq = 12, #0000
    #             ),
    #             Config.EFieldStatic(
    #                 external_E_field = efield_initial
    #             )
    #         ],
    #         step3_rampNPE = [
    #             Config.General(
    #                 method       = 'lf',
    #                 n_thermalize = 10, #0000
    #                 n_average    = 0,
    #                 n_coord_freq = 10, #0000
    #             ),
    #             Config.EFieldDynamic(
    #                 n_hl_freq        = 1, #00
    #                 n_E_wave_period  = 4, #100000,
    #                 E_wave_type      = 'ramping_off',
    #                 external_E_field = efield_initial
    #             )
    #         ],
    #         step4_postNPE = [
    #             Config.General(
    #                 method       = 'lf',
    #                 n_thermalize = 0,
    #                 n_average    = 18, #0000
    #                 n_coord_freq = 18, #0000
    #             ),
    #             Config.EFieldStatic(
    #                 external_E_field = efield_final
    #             )
    #         ]
    #     )
    # )

import os
import shutil
import colors
from pathlib import Path
from typing import cast

from src.lib.Util import src_root
from src.lib.Config import *
from src.lib.control import Temperature, ECE
from src.lib.materials.BTO import BTO


if __name__ == "__main__":
    SIM_NAME = 'bto'
    # FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'   # FERAM_BIN = Path('feram')
    FERAM_BIN = Path(cast(str, shutil.which('feram')))


    # test_path = src_root()/'test'/'temp'
    # os.makedirs(test_path, exist_ok=True)
    #
    # config = FeramConfig(
    #     setup = merge_setups([
    #         General(
    #             verbose      = 1,
    #             L            = '2 2 2',
    #             n_thermalize = 1,
    #             n_average    = 4,
    #             n_coord_freq = 1,
    #             bulk_or_film = 'epit'
    #         ),
    #         EFieldStatic(
    #             external_E_field = '0.001 0 0'
    #         ),
    #         Strain(
    #             epi_strain = '0.01 0.01 0'
    #         )
    #     ]),
    #     material = BTO
    # )
    #
    # res = Temperature.run(
    #     config, SIM_NAME, FERAM_BIN, test_path,
    #     Ti=10, Tf=20, dT=5)


    test_path = src_root()/'test'/'ece'
    os.makedirs(test_path, exist_ok=True)

    material       = BTO
    temperature    = 200
    size           = '2 2 2'
    efield_initial = '0.001 0 0'
    efield_final   = '0 0 0'

    res = ECE.run(
        SIM_NAME,
        FERAM_BIN,
        test_path,
        ECE.ECEConfig(
            material = material,
            step1_preNPT = [
                General(
                    method       = 'md',
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 0,
                    n_average    = 8, #0000
                    n_coord_freq = 8, #0000
                ),
                EFieldStatic(
                    external_E_field = efield_initial
                )
            ],
            step2_preNPE = [
                General(
                    method       = 'lf',
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 0,
                    n_average    = 12, #0000
                    n_coord_freq = 12, #0000
                ),
                EFieldStatic(
                    external_E_field = efield_initial
                )
            ],
            step3_rampNPE = [
                General(
                    method       = 'lf',
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 10, #0000
                    n_average    = 0,
                    n_coord_freq = 10, #0000
                ),
                EFieldDynamic(
                    n_hl_freq        = 1, #00
                    n_E_wave_period  = 4, #100000,
                    E_wave_type      = 'ramping_off',
                    external_E_field = efield_initial
                )
            ],
            step4_postNPE = [
                General(
                    method       = 'lf',
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 0,
                    n_average    = 18, #0000
                    n_coord_freq = 18, #0000
                ),
                EFieldStatic(
                    external_E_field = efield_final
                )
            ]
        )
    )

    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

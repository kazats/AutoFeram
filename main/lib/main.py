from pathlib import Path

import Config
from materials.BTO import BTO
import Control


if __name__ == "__main__":
    SIM_NAME = 'bto'
    FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'
    # FERAM_BIN = Path('feram')

    # config = Config.FeramConfig(
    #     setup = Config.SetupStaticElecField(
    #         verbose      = 1,
    #         L            = '2 2 2',
    #         n_thermalize = 1,
    #         n_average    = 4,
    #         n_coord_freq = 1,
    #         external_E_field = '0.001 0 0',
    #     ),
    #     material = BTO
    # )
    # config.write_feram_file(SIM_NAME)
    # Control.control_temperature(config, SIM_NAME, FERAM_BIN, Ti=10, Tf=20, dT=5)

    temperature = 200

    params = {'material':                      BTO,
              'initial_Efield':                '0.001 0 0',
              'final_Efield':                  '0 0 0',
              'kelvin':                        temperature,
              'L':                             '1 1 1',
              'n_thermalize_step1_preNPT':     0,
              'n_average_step1_preNPT':        8, #0000,
              'n_coord_freq_step1_preNPT':     8, #0000,
              'n_thermalize_step2_preNPE':     0,
              'n_average_step2_preNPE':        12, #0000,
              'n_coord_freq_step2_preNPE':     12, #0000,
              'n_thermalize_step3_rampNPE':    10, #0000,
              'n_average_step3_rampNPE':       0,
              'n_coord_freq_step3_rampNPE':    10, #0000,
              'n_hl_freq_step3_rampNPE':       1, #00,
              'n_E_wave_period_step3_rampNPE': 4, #100000,
              'E_wave_type_step3_rampNPE':     'ramping_off',
              'n_thermalize_step4_postNPE':    0,
              'n_average_step4_postNPE':       18, #0000,
              'n_coord_freq_step4_postNPE':    18, #0000,
              }


    Control.measure_electrocaloriceffect(SIM_NAME, FERAM_BIN, params)

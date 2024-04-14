from pathlib import Path

import Config
from materials.BTO import BTO
import Control


if __name__ == "__main__":
    SIM_NAME = 'bto'
    FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'
    # FERAM_BIN = Path('feram')

    config = Config.FeramConfig(
        setup = Config.SetupStaticElecField(
            verbose      = 1,
            L            = '2 2 2',
            n_thermalize = 1,
            n_average    = 4,
            n_coord_freq = 1,
            external_E_field = '0.001 0 0',
        ),
        material = BTO
    )
    # config.write_feram_file(SIM_NAME)
    # Control.control_temperature(config, SIM_NAME, FERAM_BIN, Ti=10, Tf=20, dT=5)
    Control.measure_electrocaloriceffect(config, SIM_NAME, FERAM_BIN)

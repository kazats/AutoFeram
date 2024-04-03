import FeramConfig
import Control
import subprocess as spb
from dataclasses import dataclass, field, asdict, make_dataclass
from pathlib import Path

NAME = 'bto'
BIN_FERAM = '~/Code/git/AutoFeram/feram-0.26.04/build_20240401/src/feram'

if __name__ == "__main__":
    config = FeramConfig.FeramConfig(
        setup = FeramConfig.SetupConfig(
            verbose = 1,
            L = '2 2 2',
            n_thermalize = 1,
            n_average = 4,
            n_coord_freq = 1,
        ),
        material = FeramConfig.bto
    )
    FeramConfig.write_to_file(asdict(config), NAME)
    Control.ThermoControl(config, NAME, BIN_FERAM, Ti=10, Tf=20, dT=5)

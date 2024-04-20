import os
import subprocess as sp
import shutil
from pathlib import Path
from dataclasses import dataclass

from src.lib import Config
from src.lib.Operations import *


@dataclass
class ECEConfig:
    material:      Config.Material
    step1_preNPT:  list[Config.Setup]
    step2_preNPE:  list[Config.Setup]
    step3_rampNPE: list[Config.Setup]
    step4_postNPE: list[Config.Setup]


def measure_ece(
    sim_name:  str,
    feram_bin: Path,
    ece_config: ECEConfig
    ):
    """Electrocaloric Effect"""

    def add_setups(setups: list[Config.Setup]) -> Config.FeramConfig:
        return Config.FeramConfig(
            setup    = Config.merge_setups(setups),
            material = ece_config.material
        )

    cwd           = Path.cwd()
    step1_preNPT  = cwd / '1_preNPT'
    step2_preNPE  = cwd / '2_preNPE'
    step3_rampNPE = cwd / '3_rampNPE'
    step4_postNPE = cwd / '4_postNPE'

    [ os.makedirs(step, exist_ok=True)
        for step
        in [step1_preNPT, step2_preNPE, step3_rampNPE, step4_postNPE] ]


    os.chdir(step1_preNPT)

    config          = add_setups(ece_config.step1_preNPT)
    feram_file      = step1_preNPT / f'{sim_name}.feram'
    last_coord_file = step1_preNPT / f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = step2_preNPE / f'{sim_name}.restart'

    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)

    shutil.copy2(last_coord_file, restart_file)   # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")


    os.chdir(step2_preNPE)

    config          = add_setups(ece_config.step2_preNPE)
    feram_file      = step2_preNPE / f'{sim_name}.feram'
    last_coord_file = step2_preNPE / f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = step3_rampNPE / f'{sim_name}.restart'

    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)

    shutil.copy2(last_coord_file, restart_file)


    # os.chdir(step3_rampNPE)
    # config = add_setups(ece_config.step3_rampNPE)
    # last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    # config.write_feram_file(feram_file)
    # sp.run([feram_bin, feram_file], check=True)
    # os.chdir(cwd)
    # shutil.copy2(step3_rampNPE / last_coord_file, step4_postNPE / restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")
    #
    #
    # os.chdir(step4_postNPE)
    # config = add_setups(ece_config.step3_rampNPE)
    # last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    # config.write_feram_file(feram_file)
    # sp.run([feram_bin, feram_file], check=True)
    # os.chdir(cwd)
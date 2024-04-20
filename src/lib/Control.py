import os
import subprocess as sp
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict

from src.lib import Config


def control_temperature(
    config: Config.FeramConfig,
    sim_name: str,
    feram_bin: Path,
    Ti: int,
    Tf: int,
    dT: int
    ):
    os.makedirs(Path.cwd() / 'dipoRavg', exist_ok=True)
    os.makedirs(Path.cwd() / 'coords', exist_ok=True)

    for temperature in range(Ti, Tf, dT):
        cwd = Path.cwd()
        feram_file         = cwd / f'{sim_name}.feram'
        avg_file           = cwd / f'{sim_name}.avg'
        thermo_file        = cwd / 'thermo.avg'
        dipoRavg_file      = cwd / f'{sim_name}.dipoRavg'
        temp_dipoRavg_file = cwd / 'dipoRavg' / f'{temperature}.dipoRavg'
        last_coord_file    = cwd / f'{sim_name}.{config.last_coord()}.coord'
        restart_file       = cwd / f'{sim_name}.restart'
        temp_coord_file    = cwd / 'coords' / f'{temperature}.coord'


        config.setup['kelvin'] = temperature
        config.write_feram_file(feram_file)


        sp.run([feram_bin, feram_file], check=True)

        # good?
        with open(avg_file, 'r') as inf,\
            open(thermo_file, 'a+') as outf:
            outf.write(inf.read())                      # sp.call(f"cat {name}.avg >> thermo.avg", shell=True)

        os.remove(avg_file)                             # sp.call(f"rm {name}.avg", shell=True)
        os.rename(dipoRavg_file, temp_dipoRavg_file)    # sp.call(f"mv {sim_name}.dipoRavg ./dipoRavg/{temperature}.dipoRavg", shell=True)
        shutil.copy2(last_coord_file, restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")
        os.rename(last_coord_file, temp_coord_file)     # sp.call(f"mv ./{sim_name}.{config.last_coord()}.coord ./coords/{temperature}.coord", shell=True)

    # spb.call(f"rm {NAME}.restart", shell=True)


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

    cwd = Path.cwd()
    step1_preNPT  = cwd / '1_preNPT'
    step2_preNPE  = cwd / '2_preNPE'
    step3_rampNPE = cwd / '3_rampNPE'
    step4_postNPE = cwd / '4_postNPE'

    [ os.makedirs(step, exist_ok=True) for step in [step1_preNPT, step2_preNPE, step3_rampNPE, step4_postNPE] ]

    def add_setups(setups: list[Config.Setup]) -> Config.FeramConfig:
        return Config.FeramConfig(
            setup    = Config.merge_setups(setups),
            material = ece_config.material
        )

    os.chdir(step1_preNPT)
    config = add_setups(ece_config.step1_preNPT)
    feram_file      = f'{sim_name}.feram'
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = f'{sim_name}.restart'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)
    shutil.copy2(step1_preNPT / last_coord_file, step2_preNPE / restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")

    os.chdir(step2_preNPE)
    config = add_setups(ece_config.step2_preNPE)
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)
    shutil.copy2(step2_preNPE / last_coord_file, step3_rampNPE / restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")

    os.chdir(step3_rampNPE)
    config = add_setups(ece_config.step3_rampNPE)
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)
    shutil.copy2(step3_rampNPE / last_coord_file, step4_postNPE / restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")

    os.chdir(step4_postNPE)
    config = add_setups(ece_config.step3_rampNPE)
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)


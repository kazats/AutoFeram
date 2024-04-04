import os
import subprocess as sp
import shutil
from pathlib import Path

from Config import FeramConfig


def control_temperature(
    config: FeramConfig,
    sim_name: str,
    feram_bin: Path,
    Ti: int,
    Tf: int,
    dT: int
    ):
    os.makedirs(Path.cwd() / 'dipoRavg', exist_ok=True)
    os.makedirs(Path.cwd() / 'coords', exist_ok=True)

    for temperature in range(Ti, Tf, dT):
        avg_file           = Path.cwd() / f'{sim_name}.avg'
        thermo_file        = Path.cwd() / 'thermo.avg'
        dipoRavg_file      = Path.cwd() / f'{sim_name}.dipoRavg'
        temp_dipoRavg_file = Path.cwd() / 'dipoRavg' / f'{temperature}.dipoRavg'
        last_coord_file    = Path.cwd() / f'{sim_name}.{config.last_coord()}.coord'
        restart_file       = Path.cwd() / f'{sim_name}.restart'
        temp_coord_file    = Path.cwd() / 'coords' / f'{temperature}.coord'


        config.setup.kelvin = temperature
        config.write_feram_file(sim_name)


        sp.run([feram_bin, f'{sim_name}.feram'], check=True)

        # good?
        with open(avg_file, 'r') as inf,\
            open(thermo_file, 'a+') as outf:
            outf.write(inf.read())                      # sp.call(f"cat {name}.avg >> thermo.avg", shell=True)

        os.remove(avg_file)                             # sp.call(f"rm {name}.avg", shell=True)
        os.rename(dipoRavg_file, temp_dipoRavg_file)    # sp.call(f"mv {sim_name}.dipoRavg ./dipoRavg/{temperature}.dipoRavg", shell=True)
        shutil.copy2(last_coord_file, restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")
        os.rename(last_coord_file, temp_coord_file)     # sp.call(f"mv ./{sim_name}.{config.last_coord()}.coord ./coords/{temperature}.coord", shell=True)

    # spb.call(f"rm {NAME}.restart", shell=True)

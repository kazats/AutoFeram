from Config import FeramConfig
from dataclasses import asdict
import os
from pathlib import Path
import subprocess as sp
import shutil


def control_temperature(
    config: FeramConfig,
    sim_name: str,
    feram_bin: Path,
    Ti: int,
    Tf: int,
    dT: int
    ):
    os.makedirs(Path.cwd() / 'dipoRavg', exist_ok=True) # sp.call("mkdir dipoRavg", shell=True)
    os.makedirs(Path.cwd() / 'coords', exist_ok=True) # sp.call("mkdir coords", shell=True)

    for temperature in range(Ti, Tf, dT):
        config.setup.kelvin = temperature # setattr(config.setup, 'kelvin', temperature)
        print(asdict(config.setup))
        config.write_feram_file(sim_name)

        avg_file    = Path.cwd() / f'{sim_name}.avg'
        thermo_file = Path.cwd() / 'thermo.avg'

        sp.run([feram_bin, f'{sim_name}.feram'], check=True)

        # sp.call(f"cat {name}.avg >> thermo.avg", shell=True)
        with open(avg_file, 'r') as inf,\
            open(thermo_file, 'a+') as outf:
            outf.write(inf.read())

        os.remove(avg_file) # sp.call(f"rm {name}.avg", shell=True)
        os.rename(f'{sim_name}.dipoRavg', Path.cwd() / 'dipoRavg' / f'{temperature}.dipoRavg') # sp.call(f"mv {sim_name}.dipoRavg ./dipoRavg/{temperature}.dipoRavg", shell=True)

        # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")
        shutil.copy2(Path.cwd() / f'{sim_name}.{config.last_coord()}.coord',
                     Path.cwd() / f'{sim_name}.restart',)

        # sp.call(f"mv ./{sim_name}.{config.last_coord()}.coord ./coords/{temperature}.coord", shell=True)
        os.rename(Path.cwd() / f'{sim_name}.{config.last_coord()}.coord',
                  Path.cwd() / 'coords' / f'{temperature}.coord') # sp.call(f"mv {sim_name}.dipoRavg ./dipoRavg/{temperature}.dipoRavg", shell=True)

    # spb.call(f"rm {NAME}.restart", shell=True)

import os
import FeramConfig 
from dataclasses import dataclass, field, asdict, make_dataclass
from pathlib import Path
import subprocess as spb



def last_coord(config):
    n_thermalize = getattr(config.setup, 'n_thermalize')
    n_average = getattr(config.setup, 'n_average')
    _ = str(n_thermalize + n_average)
    return _.zfill(10)

def ThermoControl(config, NAME, BIN_FERAM, Ti, Tf, dT):
    spb.call("mkdir dipoRavg", shell=True)
    spb.call("mkdir coords", shell=True)
    for temperature in range(Ti, Tf, dT):
        setattr(config.setup, 'kelvin', temperature)
        print(asdict(config.setup))
        FeramConfig.write_to_file(asdict(config), NAME)
        spb.call(f"{BIN_FERAM} {NAME}.feram", shell=True)
        spb.call(f"cat {NAME}.avg >> thermo.avg", shell=True)
        spb.call(f"rm {NAME}.avg", shell=True)
        spb.call(f"mv {NAME}.dipoRavg ./dipoRavg/{temperature}.dipoRavg", shell=True)
        spb.call(f"cp ./{NAME}.{last_coord(config)}.coord ./{NAME}.restart",shell=True)
        spb.call(f"mv ./{NAME}.{last_coord(config)}.coord ./coords/{temperature}.coord", shell=True)
    # spb.call(f"rm {NAME}.restart", shell=True)



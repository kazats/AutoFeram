from pathlib import Path

from src.lib import Config
from src.lib.Operations import *


def control_temperature(
    config: Config.FeramConfig,
    sim_name: str,
    feram_bin: Path,
    dst: Path,
    Ti: int,
    Tf: int,
    dT: int
    ):

    feram_file      = dst / f'{sim_name}.feram'
    avg_file        = dst / f'{sim_name}.avg'
    thermo_file     = dst / 'thermo.avg'
    dipoRavg_file   = dst / f'{sim_name}.dipoRavg'
    last_coord_file = dst / f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = dst / f'{sim_name}.restart'

    res = OperationSequence([
        MkDirs(DirOut(dst / 'dipoRavg')),
        MkDirs(DirOut(dst / 'coords'))
    ]).run()

    if res.is_err():
        return

    for temperature in range(Ti, Tf, dT):
        temp_dipoRavg_file = dst / 'dipoRavg' / f'{temperature}.dipoRavg'
        temp_coord_file    = dst / 'coords' / f'{temperature}.coord'

        config.setup['kelvin'] = temperature
        config.write_feram_file(feram_file)

        res = OperationSequence([
            Feram(Exec(feram_bin), FileIn(feram_file)),
            Append(FileIn(avg_file), FileOut(thermo_file)),
            Remove(FileIn(avg_file)),
            Rename(FileIn(dipoRavg_file), FileOut(temp_dipoRavg_file)),
            Copy(FileIn(last_coord_file), FileOut(restart_file)),
            Rename(FileIn(last_coord_file), FileOut(temp_coord_file)),
            # Cat(FileIn(Path('fff')))
        ]).run()

        if res.is_err():
            return

    # spb.call(f"rm {NAME}.restart", shell=True)

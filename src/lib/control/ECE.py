from pathlib import Path
from dataclasses import dataclass
from result import is_err
from itertools import zip_longest

from src.lib.Config import *
from src.lib.Operations import *


@dataclass
class ECEConfig:
    material:      Material
    step1_preNPT:  list[Setup]
    step2_preNPE:  list[Setup]
    step3_rampNPE: list[Setup]
    step4_postNPE: list[Setup]


def run(
    sim_name:  str,
    feram_bin: Path,
    dst: Path,
    ece_config: ECEConfig
    ):
    """Electrocaloric Effect"""

    def setup_with(setups: list[Setup]) -> FeramConfig:
        return FeramConfig(
            setup    = merge_setups(setups),
            material = ece_config.material
        )

    steps = [
        (dst / '1_preNPT',  ece_config.step1_preNPT),
        (dst / '2_preNPE',  ece_config.step2_preNPE),
        (dst / '3_rampNPE', ece_config.step3_rampNPE),
        (dst / '4_postNPE', ece_config.step4_postNPE)
    ]

    res = OperationSequence([MkDirs(DirOut(dir))
        for dir, _ in steps]).run()

    if is_err(res):
        return res


    for (dir, setups), (dir_next, _) in zip_longest(steps, steps[1:], fillvalue=(Any, Any)):
        config          = setup_with(setups)
        feram_file      = dir / f'{sim_name}.feram'
        last_coord_file = dir / f'{sim_name}.{config.last_coord()}.coord'
        maybe_copy      = Copy(FileIn(last_coord_file),
                               FileOut(dir_next / f'{sim_name}.restart'))\
                            if dir_next is not Any else Empty()

        res = OperationSequence([
            Write(FileOut(feram_file),
                  config.generate_feram_file),
            WithDir(DirIn(dst),
                    DirIn(dir),
                    Feram(Exec(feram_bin),
                          FileIn(feram_file))),
            maybe_copy
        ]).run()

        if is_err(res):
            return res

    return Ok('Measure ECE: success')

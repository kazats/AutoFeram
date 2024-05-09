import os
import shutil
import colors
from result import is_err
from pathlib import Path
from dataclasses import dataclass
from itertools import zip_longest
from typing import cast

from src.lib.common import Vec3
from src.lib.control import ECE
from src.lib.materials.BTO import BTO
from src.lib.Config import *
from src.lib.Util import project_root
from src.lib.Log import *
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


if __name__ == "__main__":
    SIM_NAME = 'bto'
    # FERAM_BIN = Path.home() / 'Code' / 'git' / 'AutoFeram' / 'feram-0.26.04' / 'build_20240401' / 'src' / 'feram'   # FERAM_BIN = Path('feram')
    FERAM_BIN = Path(cast(str, shutil.which('feram')))


    out_path = project_root() / 'output' / 'ece'
    os.makedirs(out_path, exist_ok=True)

    material       = BTO
    temperature    = 200
    size           = Vec3(2, 2, 2)
    efield_initial = Vec3(0.001, 0, 0)
    efield_final   = Vec3[float](0, 0, 0)

    res = ECE.run(
        SIM_NAME,
        FERAM_BIN,
        out_path,
        ECE.ECEConfig(
            material = material,
            step1_preNPT = [
                General(
                    method       = Method.MD,
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 0,
                    n_average    = 8, #0000
                    n_coord_freq = 8, #0000
                ),
                EFieldStatic(
                    external_E_field = efield_initial
                )
            ],
            step2_preNPE = [
                General(
                    method       = Method.LF,
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 0,
                    n_average    = 12, #0000
                    n_coord_freq = 12, #0000
                ),
                EFieldStatic(
                    external_E_field = efield_initial
                )
            ],
            step3_rampNPE = [
                General(
                    method       = Method.LF,
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 10, #0000
                    n_average    = 0,
                    n_coord_freq = 10, #0000
                ),
                EFieldDynamic(
                    n_hl_freq        = 1, #00
                    n_E_wave_period  = 4, #100000,
                    E_wave_type      = EWaveType.RampOff,
                    external_E_field = efield_initial
                )
            ],
            step4_postNPE = [
                General(
                    method       = Method.LF,
                    kelvin       = temperature,
                    L            = size,
                    n_thermalize = 0,
                    n_average    = 18, #0000
                    n_coord_freq = 18, #0000
                ),
                EFieldStatic(
                    external_E_field = efield_final
                )
            ]
        )
    )

    color_res = colors.yellow(res) if res.is_ok() else colors.red(res)
    print(color_res)

    # post processing
    # log_path  = out_path / 'bto.log'
    # log_raw   = read_log(log_path)
    # log       = parse_log(log_raw)
    # res       = post_process(log, config)

    # print(res)
    # print(len(res))

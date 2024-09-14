from pathlib import Path
from itertools import zip_longest

from src.lib.common import *
from src.lib.control import ECE
from src.lib.control.common import *
from src.lib.Config import *
from src.lib.Domain import *
from src.lib.Materials import BTO
from src.lib.Operations import *
from src.lib.Ovito import WriteOvito
from src.lib.Util import *



if __name__ == "__main__":
    runner = Runner(
        sim_name    = 'bto',
        feram_path  = Path.home() / 'feram_dev/build/src/feram',
        output_dir = project_root() / 'output' / f'ece_{timestamp()}'
    )

    efield_initial = Vec3(0.0007071067811865476, 0.0007071067811865475 ,6.123233995736766e-20)
    efield_final   = Vec3(0.0, 0, 0)        # efield_final should be Vec3(0.0, 0, 0) when EWaveType.RampOff is used in '3_rampNPE'
    temperature = 380

    common = {
        GeneralProps.L(Int3(36, 36, 36)),
        GeneralProps.kelvin(temperature)
    }

    config = ece_config(
        material = BTO,
        common = common,
        steps = {
            '1_preNPT': [
                General(
                    method       = Method.MD,
                    n_thermalize = 0,
                    n_average    = 8, #0000,
                    n_coord_freq = 2, #0000,
                ),
                EFieldStatic(external_E_field = efield_initial)
            ],
            '2_preNPE': [
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 1, #20000,
                    n_coord_freq = 2, #0000,
                ),
                EFieldStatic(external_E_field = efield_initial)
            ],
            '3_rampNPE': [
                General(
                    method       = Method.LF,
                    n_thermalize = 1, #00000,
                    n_average    = 0, #,
                    n_coord_freq = 2, #0000,
                ),
                EFieldDynamic(
                    n_hl_freq        = 1, #00,
                    n_E_wave_period  = 4, #100000,
                    E_wave_type      = EWaveType.RampOff,
                    external_E_field = efield_initial
                )
            ],
            '4_postNPE': [
                General(
                    method       = Method.LF,
                    n_thermalize = 0,
                    n_average    = 1, #80000,
                    n_coord_freq = 2, #0000,
                ),
                EFieldStatic(external_E_field = efield_final)
            ]
        })

    initial_coord = project_root() / 'output' / f'temperature_2024-09-14/coords/{temperature}.coord'
    copy_initialcoord = Copy(FileIn(initial_coord), FileOut(runner.output_dir / '1_preNPT' / f'{runner.sim_name}.restart'))

    exit_from_result(ECE.run(runner, config, add_pre = copy_initialcoord))

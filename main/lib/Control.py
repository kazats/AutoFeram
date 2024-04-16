import os
import subprocess as sp
import shutil
from pathlib import Path

from Config import FeramConfig
import Config


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


def measure_electrocaloriceffect(
    sim_name:  str,
    feram_bin: Path,
    params:    dict
    ):

    cwd = Path.cwd()
    step1_preNPT  = cwd / '1_preNPT'
    step2_preNPE  = cwd / '2_preNPE'
    step3_rampNPE = cwd / '3_rampNPE'
    step4_postNPE = cwd / '4_postNPE'


    [ os.makedirs(step, exist_ok=True) for step in [step1_preNPT, step2_preNPE, step3_rampNPE, step4_postNPE] ]

    os.chdir(step1_preNPT)
    config = Config.FeramConfig(
        setup = Config.SetupStaticElecField(
            n_thermalize = params['n_thermalize_step1_preNPT'],
            n_average    = params['n_average_step1_preNPT'],
            n_coord_freq = params['n_coord_freq_step1_preNPT'],
            external_E_field = params['initial_Efield'],
        ),
        material = params['material']
    )
    feram_file      = f'{sim_name}.feram'
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    restart_file    = f'{sim_name}.restart'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)
    shutil.copy2(step1_preNPT / last_coord_file, step2_preNPE / restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")

    os.chdir(step2_preNPE)
    config = Config.FeramConfig(
        setup = Config.SetupStaticElecField(
            method       = 'lf',
            n_thermalize = params['n_thermalize_step2_preNPE'],
            n_average    = params['n_average_step2_preNPE'],
            n_coord_freq = params['n_coord_freq_step2_preNPE'],
            external_E_field = params['initial_Efield'],
        ),
        material = params['material']
    )
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)
    shutil.copy2(step2_preNPE / last_coord_file, step3_rampNPE / restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")

    os.chdir(step3_rampNPE)
    config = Config.FeramConfig(
        setup = Config.SetupDynamicElecField(
            method          = 'lf',
            n_thermalize    = params['n_thermalize_step3_rampNPE'],
            n_average       = params['n_average_step3_rampNPE'],
            n_coord_freq    = params['n_coord_freq_step3_rampNPE'],
            n_hl_freq       = params['n_hl_freq_step3_rampNPE'],
            n_E_wave_period = params['n_E_wave_period_step3_rampNPE'],
            E_wave_type     = params['E_wave_type_step3_rampNPE'],
            external_E_field = params['initial_Efield']
        ),
        material =  params['material']
    )
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)
    shutil.copy2(step3_rampNPE / last_coord_file, step4_postNPE / restart_file)     # sp.call(f"cp ./{sim_name}.{config.last_coord()}.coord ./{sim_name}.restart")

    os.chdir(step4_postNPE)
    config = Config.FeramConfig(
        setup = Config.SetupStaticElecField(
            method           = 'lf',
            n_thermalize     = params['n_thermalize_step4_postNPE'],
            n_average        = params['n_average_step4_postNPE'],
            n_coord_freq     = params['n_coord_freq_step4_postNPE'],
            external_E_field = params['final_Efield']
        ),
        material =  params['material']
    )
    last_coord_file = f'{sim_name}.{config.last_coord()}.coord'
    config.write_feram_file(feram_file)
    sp.run([feram_bin, feram_file], check=True)
    os.chdir(cwd)


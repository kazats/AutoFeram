from pathlib import Path

FERAM_INPUT_FILE = Path.cwd() / Path('test.feram')

CONFIG = {
    'setup': {
        'verbose': '4',
        'method': "'vs'",
        'GPa': '$GPa',
        'kelvin': '$temperature',
        'Q_Nose': '15'
    },
    'geometry': {
        'bulk_or_film': "'bulk'",
        'L': '32 32 32'
    },
    'time_steps': {
        'dt': '0.002 [pico second]',
        'n_thermalize': '$n_thermalize',
        'n_average': '$n_average',
        'n_coord_freq': '$n_coord_freq',
        'distribution_directory': "'never'"
    },
    'initial_dipole': {
        'init_dipo_avg': '0.0   0.0   0.0    [Angstrom]  # Average   of initial dipole displacements',
        'init_dipo_dev': '0.02  0.02  0.02   [Angstrom]  # Deviation of initial dipole displacements'
    },
    'material': {
        'modulation_constant': '-0.279',
        'B11': '129.0286059',
        'B12': '39.00720516',
        'B44': '45.26949109',
        'B1xx': '-143.7185938',
        'B1yy': '-1.375464746',
        'B4yz': '-15.02208695',
        'P_k1': '-166.56247',
        'P_k2': '157.2518592',
        'P_k3': '515.9414896',
        'P_k4': '390.6570497',
        'P_alpha': '50.68630712',
        'P_gamma': '-72.18357441',
        'P_kappa2': '9.4250031',
        'j': '-2.048250285  -1.472144446  0.6396521198  -0.5891190367  0.0 0.2576732039  0.0',
        'a0': '3.9435    [Angstrom]',
        'Z_star': '9.807238756',
        'epsilon_inf': '6.663371926',
        'mass_amu': '40.9285',
        'acoustic_mass_amu': '41.67'
    }
}

def update_config(default_config, custom_config):
    return {s: default_config[s] | custom_config.get(s, {}) for s in default_config.keys()}
    # return default_config | custom_config

def generate_key_val(k: str, v: str):
    return f"{k} = {v}"

def loop_dict(d: dict):
    for k, v in d.items():
        yield f"# {k}"

        for vk, vv in v.items():
            yield generate_key_val(vk, vv)

        yield ""
    # return (generate_key_val(k, v) for k, v in d.items())
    # for k, v in d.items():
    #     yield generate_key_val(k, v)

def write_to_file(config, filepath=FERAM_INPUT_FILE):
    with open(filepath, 'w') as feram_input_file:
        for i in loop_dict(config):
            feram_input_file.write(f"{i}\n")

if __name__ == "__main__":
    custom_config = {
        'setup': {
            'verbose': 1
        }
    }
    write_to_file(update_config(CONFIG, custom_config), FERAM_INPUT_FILE)

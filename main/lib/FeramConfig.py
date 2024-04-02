from dataclasses import dataclass, field, asdict
from pathlib import Path

FERAM_INPUT_FILE = Path.cwd() / Path('test.feram')

@dataclass
class SetupConfig:
    verbose: int                = 4
    method: str                 = 'md'
    GPa: float                  = 0
    kelvin: int                 = 300
    Q_Nose: float               = 15
    bulk_or_film: str           = 'bulk'
    L: str                      = '32 32 32'
    dt: float                   = 0.002
    n_thermalize: str           = '$n_thermalize'
    n_average: str              = '$n_average'
    n_coord_freq: str           = '$n_coord_freq'
    distribution_directory: str = 'never'
    init_dipo_avg: str          = '0.0   0.0   0.0' # [Angstrom] Average of initial dipole displacements
    init_dipo_dev: str          = '0.02  0.02  0.02' # [Angstrom] Deviation of initial dipole displacement

@dataclass
class MaterialConfig:
    modulation_constant: float = -0.279
    B11: float                 = 129.0286059
    B12: float                 = 39.00720516
    B44: float                 = 45.26949109
    B1xx: float                = -143.7185938
    B1yy: float                = -1.375464746
    B4yz: float                = -15.02208695
    P_k1: float                = -166.56247
    P_k2: float                = 157.2518592
    P_k3: float                = 515.9414896
    P_k4: float                = 390.6570497
    P_alpha: float             = 50.68630712
    P_gamma: float             = -72.18357441
    P_kappa2: float            = 9.4250031
    j: str                     = '-2.048250285  -1.472144446  0.6396521198  -0.5891190367  0.0 0.2576732039  0.0'
    a0: float                  = 3.9435 # [Angstrom]
    Z_star: float              = 9.807238756
    epsilon_inf: float         = 6.663371926
    mass_amu: float            = 40.9285
    acoustic_mass_amu: float   = 41.6

@dataclass
class FeramConfig:
    setup: SetupConfig = field(default_factory=SetupConfig)
    material: MaterialConfig = field(default_factory=MaterialConfig)

BST = MaterialConfig(
    modulation_constant = -0.279,
    B11 = 129.0286059,
    B12 = 39.00720516,
    B44 = 45.26949109,
    B1xx = -143.7185938,
    B1yy = -1.375464746,
    B4yz = -15.02208695,
    P_k1 = -166.56247,
    P_k2 = 157.2518592,
    P_k3 = 515.9414896,
    P_k4 = 390.6570497,
    P_alpha = 50.68630712,
    P_gamma = -72.18357441,
    P_kappa2 = 9.4250031,
    j = '-2.048250285  -1.472144446  0.6396521198  -0.5891190367  0.0 0.2576732039  0.0',
    a0 = 3.9435,
    Z_star = 9.807238756,
    epsilon_inf = 6.663371926,
    mass_amu = 40.9285,
    acoustic_mass_amu = 41.6
)

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
    config = FeramConfig(
        setup = SetupConfig(
            verbose = 1
        ),
        material = BST
    )
    # print(asdict(config))
    write_to_file(asdict(config), FERAM_INPUT_FILE)

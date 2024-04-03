from dataclasses import dataclass, field, asdict, make_dataclass
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
    L: str                      = '36 36 36'
    dt: float                   = 0.002
    n_thermalize: int           = 40000
    n_average: int              = 20000
    n_coord_freq: int           = 60000
    distribution_directory: str = 'never'
    init_dipo_avg: str          = '0.0   0.0   0.0' # [Angstrom] Average of initial dipole displacements
    init_dipo_dev: str          = '0.02  0.02  0.02' # [Angstrom] Deviation of initial dipole displacement

@dataclass
class MaterialConfig:  # parameters are from BTO
    mass_amu: float    = 38.24
    a0 : float         = 3.98597 #    [Angstrom],
    Z_star : float     = 10.33000
    B11: float         = 126.731671475652
    B12: float         = 41.7582963902598
    B44: float         = 49.2408864348646
    B1xx: float        = -185.347187551195 # [eV/Angstrom^2],
    B1yy: float        = -3.28092949275457 # [eV/Angstrom^2],
    B4yz: float        = -14.5501738943852 # [eV/Angstrom^2],
    P_k1: float        = -267.98013991724 # [eV/Angstrom^6],
    P_k2: float        = 197.500718362573 # [eV/Angstrom^6],
    P_k3: float        = 830.199979293529 # [eV/Angstrom^6],
    P_k4: float        = 641.968099408642 # [eV/Angstrom^8],
    P_alpha: float     = 78.9866142426818 # [eV/Angstrom^4],
    P_gamma: float     = -115.484148812672 # [eV/Angstrom^4],
    P_kappa2: float    = 8.53400622096412
    j: str             = '-2.08403 -1.12904  0.68946 -0.61134  0.00000  0.27690  0.00000' #    [eV/Angstrom^2],
    epsilon_inf: float = 6.86915

@dataclass
class BST(MaterialConfig):
    modulation_constant: float = -0.279
    acoustic_mass_amu: float = 41.67
bst = BST(mass_amu          = 40.9285,
          a0                = 3.9435,
          Z_star            = 9.807238756,
          B11               = 129.0286059,
          B12               = 39.00720516,
          B44               = 45.26949109,
          B1xx              = -143.7185938,
          B1yy              = -1.375464746,
          B4yz              = -15.02208695,
          P_k1              = -166.56247,
          P_k2              = 157.2518592,
          P_k3              = 515.9414896,
          P_k4              = 390.6570497,
          P_alpha           = 50.68630712,
          P_gamma           = -72.18357441,
          P_kappa2          = 9.4250031,
          j                 = '-2.048250285  -1.472144446  0.6396521198  -0.5891190367  0.0 0.2576732039  0.0',
          epsilon_inf       = 6.663371926,
          )

# BST = MaterialConfig(
#     mass_amu          = 40.9285,
#     a0                = 3.9435,
#     Z_star            = 9.807238756,
#     B11               = 129.0286059,
#     B12               = 39.00720516,
#     B44               = 45.26949109,
#     B1xx              = -143.7185938,
#     B1yy              = -1.375464746,
#     B4yz              = -15.02208695,
#     P_k1              = -166.56247,
#     P_k2              = 157.2518592,
#     P_k3              = 515.9414896,
#     P_k4              = 390.6570497,
#     P_alpha           = 50.68630712,
#     P_gamma           = -72.18357441,
#     P_kappa2          = 9.4250031,
#     j                 = '-2.048250285  -1.472144446  0.6396521198  -0.5891190367  0.0 0.2576732039  0.0',
#     epsilon_inf       = 6.663371926,
#     )
# BST.__class__ = make_dataclass('bst',
#                                fields=[('modulation_constant', float, field(default=-0.279)), 
#                                        ('acoustic_mass_amu', float, field(default=41.67))], 
#                                bases=(MaterialConfig,))


@dataclass
class FeramConfig:
    setup: SetupConfig       = field(default_factory=SetupConfig)
    material: MaterialConfig = field(default_factory=MaterialConfig)



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
        material = bst
    )
    # print(asdict(config))
    write_to_file(asdict(config), FERAM_INPUT_FILE)

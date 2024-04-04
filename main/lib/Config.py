from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Setup:
    method: str
    bulk_or_film: str
    L: str
    dt: float
    # temperature and pressure control
    GPa: float
    kelvin: int
    Q_Nose: float
    # output
    verbose: int
    n_thermalize: int
    n_average: int
    n_coord_freq: int
    distribution_directory: str
    slice_directory: str
    # coord_directory: str
    # initial dipole
    init_dipo_avg: str # [Angstrom] Average of initial dipole displacements
    init_dipo_dev: str # [Angstrom] Deviation of initial dipole displacement
    # electric field
    n_E_wave_period: int
    n_hl_freq: int
    E_wave_type: str
    external_E_field: str


# default_setup = Setup(
#     method = 'md',
#     bulk_or_film = 'bulk',
#     L = '36 36 36',
#     dt = 0.002,
#     GPa = 0,
#     kelvin = 300,
#     Q_Nose = 15,
#     verbose = 4,
#     n_thermalize = 40000,
#     n_average = 20000,
#     n_coord_freq = 60000,
#     distribution_directory = 'never',
#     slice_directory = 'never',
#     init_dipo_avg = '0.0   0.0   0.0',
#     init_dipo_dev = '0.02  0.02  0.02',
#     n_E_wave_period = 0,
#     n_hl_freq = 10000,
#     E_wave_type = 'ramping_off',
#     external_E_field = '0.00 0.00 0.00',
# )

@dataclass
class DefaultSetup(Setup):
    method = 'md'
    bulk_or_film = 'bulk'
    L = '36 36 36'
    dt = 0.002
    GPa = 0
    kelvin = 300
    Q_Nose = 15
    verbose = 4
    n_thermalize = 40000
    n_average = 20000
    n_coord_freq = 60000
    distribution_directory = 'never'
    slice_directory = 'never'
    init_dipo_avg = '0.0   0.0   0.0'
    init_dipo_dev = '0.02  0.02  0.02'
    n_E_wave_period = 0
    n_hl_freq = 10000
    E_wave_type = 'ramping_off'
    external_E_field = '0.00 0.00 0.00'


@dataclass
class Material:
    mass_amu: float
    a0 : float # [Angstrom],
    Z_star : float
    B11: float
    B12: float
    B44: float
    B1xx: float # [eV/Angstrom^2],
    B1yy: float # [eV/Angstrom^2],
    B4yz: float # [eV/Angstrom^2],
    P_k1: float # [eV/Angstrom^6],
    P_k2: float # [eV/Angstrom^6],
    P_k3: float # [eV/Angstrom^6],
    P_k4: float # [eV/Angstrom^8],
    P_alpha: float # [eV/Angstrom^4],
    P_gamma: float # [eV/Angstrom^4],
    P_kappa2: float
    j: str # [eV/Angstrom^2],
    epsilon_inf: float


@dataclass
class SolidSolution(Material):
    modulation_constant: float
    acoustic_mass_amu: float


@dataclass
class FeramConfig:
    setup: Setup
    material: Material

    def write_feram_file(self, sim_name):
        def generate_key_val(k: str, v: str):
            return f"{k} = {v}"

        def generate_feram_file(d: dict):
            for k, v in d.items():
                yield f"# {k}"

                for vk, vv in v.items():
                    yield generate_key_val(vk, vv)

                yield ""
            # return (generate_key_val(k, v) for k, v in d.items())
            # for k, v in d.items():
            #     yield generate_key_val(k, v)

        filepath = Path.cwd() / f'{sim_name}.feram'

        with open(filepath, 'w') as feram_input_file:
            for i in generate_feram_file(asdict(self)):
                feram_input_file.write(f"{i}\n")

    def last_coord(self) -> str:
        total_steps = self.setup.n_thermalize + self.setup.n_average
        return str(total_steps).zfill(10)

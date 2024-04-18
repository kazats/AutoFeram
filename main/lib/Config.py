from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Tuple


@dataclass
class Setup:
    method: str                 = 'md'
    bulk_or_film: str           = 'bulk'
    L: str                      = '36 36 36'
    dt: float                   = 0.002
    # temperature and pressure control
    GPa: float                  = 0
    kelvin: int                 = 300
    Q_Nose: float               = 15
    # output
    verbose: int                = 4
    n_thermalize: int           = 40000
    n_average: int              = 20000
    n_coord_freq: int           = 60000
    distribution_directory: str = 'never'
    slice_directory: str        = 'never'
    # initial dipole
    init_dipo_avg: str          = '0.0   0.0   0.0'  # [Angstrom] Average of initial dipole displacements
    init_dipo_dev: str          = '0.02  0.02  0.02' # [Angstrom] Deviation of initial dipole displacement


@dataclass
class SetupStrain(Setup):
    epi_strain: str = '0.00 0.00 0.00'


@dataclass
class SetupStaticElecField(Setup):
    external_E_field: str       = '0.00 0.00 0.00'


@dataclass
class SetupDynamicElecField(Setup):
    n_E_wave_period: int        = 0
    n_hl_freq: int              = 10000
    E_wave_type: str            = 'ramping_off'
    external_E_field: str       = '0.00 0.00 0.00'


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

    def write_feram_file(self, feram_file):
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

        filepath = Path.cwd() / feram_file

        with open(filepath, 'w') as feram_input_file:
            for i in generate_feram_file(asdict(self)):
                feram_input_file.write(f"{i}\n")

    def last_coord(self) -> str:
        total_steps = self.setup.n_thermalize + self.setup.n_average
        return str(total_steps).zfill(10)

    def polarization_parameters(self) -> dict:
        return {'a0': self.material.a0,
                'Z_star': self.material.Z_star,
                'factor': 1.6 * 10**3 * self.material.Z_star / self.material.a0**3}
    # factor: from displacement to polarization; physical meaning: effective charge 

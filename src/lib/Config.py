from functools import reduce
from dataclasses import dataclass, asdict
from enum import StrEnum
from collections.abc import Generator, Sequence, Mapping
from typing import Any, NamedTuple, TypeAlias

from src.lib.common import Vec3, Vec7


class Method(StrEnum):
    MD = 'md'
    LF = 'lf'
    VS = 'vs'
    HL = 'hl'

class Structure(StrEnum):
    Bulk = 'bulk'
    Film = 'film'
    Epit = 'epit'

@dataclass
class Setup:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class General(Setup):
    method: Method              = Method.MD
    bulk_or_film: Structure     = Structure.Bulk
    L: Vec3[int]                = Vec3(36, 36, 36)
    dt: float                   = 0.002

    # temperature and pressure control
    GPa: float                  = 0
    kelvin: float               = 300
    Q_Nose: float               = 15

    # output
    verbose: int                = 4
    n_thermalize: int           = 40000
    n_average: int              = 20000
    n_coord_freq: int           = 60000
    distribution_directory: str = 'never'
    slice_directory: str        = 'never'

    # initial dipole
    init_dipo_avg: Vec3[float]  = Vec3(0.0, 0.0, 0.0)    # [Angstrom] Average of initial dipole displacements
    init_dipo_dev: Vec3[float]  = Vec3(0.02, 0.02, 0.02) # [Angstrom] Deviation of initial dipole displacement


@dataclass
class Strain(Setup):
    epi_strain: Vec3[float] = Vec3(0.00, 0.00, 0.00)


@dataclass
class EFieldStatic(Setup):
    external_E_field: Vec3[float] = Vec3(0.00, 0.00, 0.00)


class EWaveType(StrEnum):
    TriSin  = 'triangular_sin'
    TriCos  = 'triangular_cos'
    RampOff = 'ramping_off'
    RampOn  = 'ramping_on'

@dataclass
class EFieldDynamic(Setup):
    n_E_wave_period: int          = 0   # must be divisible by 4 if TriSin or TriCos
    n_hl_freq: int                = 10000
    E_wave_type: EWaveType        = EWaveType.RampOff
    external_E_field: Vec3[float] = Vec3(0.00, 0.00, 0.00)


def merge_setups(setups: Sequence[Setup]) -> dict[str, Any]:
    dict_setups = map(lambda s: s.to_dict(), setups)
    return reduce(lambda acc, d: acc | d, dict_setups)


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
    j: Vec7 # [eV/Angstrom^2],
    epsilon_inf: float


@dataclass
class SolidSolution(Material):
    modulation_constant: float
    acoustic_mass_amu: float


class PolarizationParameters(NamedTuple):
    a0: float
    Z_star: float
    factor: float


SetupDict: TypeAlias = dict[str, Any]

@dataclass
class FeramConfig:
    setup: SetupDict
    material: Material

    def generate_feram_file(self) -> str:
        def generate_key_val(k: str, v: str):
            return f'{k} = {v}'

        def file_generator() -> Generator[str, None, None]:
            for k, v in asdict(self).items():
                yield f'# {k}'

                for vk, vv in v.items():
                    yield generate_key_val(vk, vv)

                yield ''
            # return (generate_key_val(k, v) for k, v in d.items())
            # for k, v in d.items():
            #     yield generate_key_val(k, v)

        return '\n'.join(file_generator())

    def last_coord(self) -> str:
        total_steps = self.setup['n_thermalize'] + self.setup['n_average']
        return str(total_steps).zfill(10)

    @property
    def polarization_parameters(self) -> PolarizationParameters:
        return PolarizationParameters(
            a0     = self.material.a0,
            Z_star = self.material.Z_star,
            factor = 1.6 * 10**3 * self.material.Z_star / self.material.a0**3   # factor: from displacement to polarization; physical meaning: effective charge
        )

from functools import reduce
from dataclasses import dataclass, asdict
from enum import StrEnum
from collections.abc import Iterable, Iterator
from typing import Any, NamedTuple, TypeAlias
import random

from src.lib.common import Int2, Int3, Vec3, Vec7
from src.lib.Util import function_name


class Method(StrEnum):
    MD = 'md'
    LF = 'lf'
    VS = 'vs'
    HL = 'hl'

class Structure(StrEnum):
    Bulk     = 'bulk'     # unstrained (periodic) bulk
    Strn_001 = 'strn_001' # bulk strained on (001) surface
    Strn_110 = 'strn_110' # bulk strained on (110) surface
    Film     = 'film'     # unstrained (free standing) film
    Epit_001 = 'epit_001' # film strained on (001) surface
    Epit_110 = 'epit_110' # film strained on (110) surface


SetupDict: TypeAlias = dict[str, Any]

@dataclass
class Setup:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class General(Setup):
    method: Method              = Method.MD
    bulk_or_film: Structure     = Structure.Bulk
    L: Int3                     = Int3(36, 36, 36)
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
    init_dipo_avg: Vec3[float]  = Vec3(0, 0, 0)          # [Angstrom] Average of initial dipole displacements
    init_dipo_dev: Vec3[float]  = Vec3(0.02, 0.02, 0.02) # [Angstrom] Deviation of initial dipole displacement

class GeneralProps:
    @staticmethod
    def method(value: Method): return function_name(), value
    @staticmethod
    def bulk_or_film(value: Structure): return function_name(), value
    @staticmethod
    def L(value: Int3): return function_name(), value
    @staticmethod
    def dt(value: float): return function_name(), value
    @staticmethod
    def GPa(value: float): return function_name(), value
    @staticmethod
    def kelvin(value: float): return function_name(), value
    @staticmethod
    def Q_Nose(value: float): return function_name(), value
    @staticmethod
    def verbose(value: int): return function_name(), value
    @staticmethod
    def n_thermalize(value: int): return function_name(), value
    @staticmethod
    def n_average(value: int): return function_name(), value
    @staticmethod
    def n_coord_freq(value: int): return function_name(), value
    @staticmethod
    def distribution_directory(value: str): return function_name(), value
    @staticmethod
    def slice_directory(value: str): return function_name(), value
    @staticmethod
    def init_dipo_avg(value: Vec3[float]): return function_name(), value
    @staticmethod
    def init_dipo_dev(value: Vec3[float]): return function_name(), value

# test = Enum(
#     value = 'test',
#     names = [('method', lambda value: ('method', value))]
# )
# class test(Enum):
#     method: Callable[[Method], tuple] = lambda value: ('method', value)


@dataclass
class Strain(Setup):                          # no deadlayer, i.e. gap_id == (feram default) 0
    epi_strain: Vec3[float] = Vec3(0, 0, 0)

@dataclass
class Film(Setup):      # for free standing or strained thin film, i.e. (in feram's terms) 'film' or 'epit'
    gap_id:       int         = 0             # gap_id: number of deadlayer (of thickness 1 nm); gap_id should be 1 or 2 for 'Film'; mod(Lz,2)==mod(gap_id,2)
    gap_dipole_u: Int3        = Int3(0, 0, 0) # polarization of deadlayers [Angstrom]

@dataclass
class EFieldStatic(Setup):
    external_E_field: Vec3[float] = Vec3(0, 0, 0)


class EWaveType(StrEnum):
    TriSin  = 'triangular_sin'
    TriCos  = 'triangular_cos'
    RampOff = 'ramping_off'
    RampOn  = 'ramping_on'

@dataclass
class EFieldDynamic(Setup):
    n_E_wave_period: int          = 0  # must be divisible by 4 if TriSin or TriCos
    n_hl_freq: int                = 10000
    E_wave_type: EWaveType        = EWaveType.RampOff
    external_E_field: Vec3[float] = Vec3(0, 0, 0)

@dataclass
class RandomSeed(Setup):
    # Feram default
    seed: Int2 = Int2(123456789, 987654321)

def generate_randomseed() -> Int2:
    # generate integers for Marsaglia-Tsang 64-bit universal RNG
    def gen() -> int:
        return random.randint(0, 32767) * 65536 + random.randint(0, 32767)

    return Int2(gen(), gen())


def merge_setups(setups: Iterable[Setup]) -> SetupDict:
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
    j: Vec7[float] # [eV/Angstrom^2],
    epsilon_inf: float


@dataclass
class SolidSolution(Material):
    modulation_constant: float
    # acoustic_mass_amu: float


class PolarizationParameters(NamedTuple):
    a0: float
    Z_star: float
    factor: float


@dataclass
class FeramConfig:
    material: Material
    setup: SetupDict

    def generate_feram_file(self) -> str:
        def generate_key_val(k: str, v: str):
            return f'{k} = {v}'

        def file_generator() -> Iterator[str]:
            for k, v in asdict(self).items():
                yield f'# {k}'

                for vk, vv in v.items():
                    yield generate_key_val(vk, vv)

                yield ''
            # return (generate_key_val(k, v) for k, v in d.items())
            # for k, v in d.items():
            #     yield generate_key_val(k, v)

        return '\n'.join(file_generator())

    @property
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

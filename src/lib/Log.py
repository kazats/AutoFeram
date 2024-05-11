import pandas as pd
from parsy import Parser, seq, any_char, whitespace, string, regex
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.lib.common import Vec3
from src.lib.Util import project_root


@dataclass
class TimeStep:
    time_step:       int
    acou_kinetic:    float
    dipo_kinetic:    float
    short_range:     float
    long_range:      float
    dipole_E_field:  float
    unharmonic:      float
    homo_strain:     float
    homo_coupling:   float
    inho_strain:     float
    inho_coupling:   float
    inho_modulation: float
    total_energy:    float
    H_Nose_Poincare: Optional[float]
    s_Nose:          Optional[float]
    pi_Nose:         Optional[float]
    u:               Optional[Vec3[float]]
    u_sigma:         Optional[Vec3[float]]
    p:               Optional[Vec3[float]]
    p_sigma:         Optional[Vec3[float]]

@dataclass
class Log:
    time_steps: list[TimeStep]

    def to_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.time_steps)


def read_log(log_path: Path) -> str:
    with open(log_path, 'r') as log:
        return log.read()

def parse_log(log: str) -> Log:
    floating       = regex(r'\-?\d+\.\d+').map(float)
    integer        = regex(r'\d+').map(int)
    any_char_until = any_char.until

    def float_element(token: str) -> Parser:
        tok = any_char_until(string(token)) >> string(token)
        flt = whitespace >> floating

        return (tok >> flt).optional().map(lambda v: (token, v)).desc(token)

    def vector_element(name: str, token: str) -> Parser:
        tok = any_char_until(string(token)) >> string(token)
        vec = whitespace >> seq(floating << whitespace, floating << whitespace, floating).map(Vec3._make)

        return (tok >> vec).optional().map(lambda v: (name, v)).desc(token)

    # ts_start    = (any_char_until(string('TIME_STEP'), consume_other=True) >> whitespace >> integer).desc('ts_start')
    ts_start    = any_char_until(string('TIME_STEP')).desc('ts_start')
    ts_end      = any_char_until(string('TIME_STEP_END'), consume_other=True).concat().desc('ts_end')
    ts_section  = (ts_start >> ts_end).desc('ts_section')
    ts_sections = ts_section.many().desc('ts_sections')
    time_step   = (string('TIME_STEP') >> whitespace >> integer).map(lambda v: ('time_step', v)).desc('time_step')

    def parse_ts_section(ts_section: str) -> TimeStep:
        ts_fields = seq(
            time_step,
            *map(float_element,
                 ['acou_kinetic',
                  'dipo_kinetic',
                  'short_range',
                  'long_range',
                  'dipole_E_field',
                  'unharmonic',
                  'homo_strain',
                  'homo_coupling',
                  'inho_strain',
                  'inho_coupling',
                  'inho_modulation',
                  'total_energy',
                  'H_Nose_Poincare',
                  's_Nose',
                  'pi_Nose']),
            *map(lambda tup: vector_element(tup[0], tup[1]),
                 [('u', '<u>'),
                  ('u_sigma', 'sigma'),
                  ('p', '<p>'),
                  ('p_sigma', 'sigma')])
        )

        return ts_fields.combine_dict(TimeStep).parse_partial(ts_section)[0]

    ts_sections_res = ts_sections.parse_partial(log)[0]

    return Log(list(map(parse_ts_section, ts_sections_res)))


if __name__ == "__main__":
    test_path = project_root() / 'output' / 'temp'
    log_path  = test_path / 'bto.log'
    log_raw   = read_log(log_path)
    log       = parse_log(log_raw)
    df        = log.to_df()

    print(df)
    print(len(df))

    # log_info = read_log(log_path)
    # disp_re = r'<u>\s*=\s*(.*?)\s+(.*?)\s+(.*?)$'
    # disp_matches: list[tuple[str, str, str]] = re.findall(disp_re, log_info, re.MULTILINE)
    # disp_vectors = list(map(lambda dv: tuple(map(float, dv)), disp_matches))
    #
    # print(disp_vectors)
    # print(len(disp_vectors))

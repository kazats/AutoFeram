import re
import pandas as pd
from pathlib import Path
from src.lib.Util import src_root


def get_log_info(log_path: Path): # -> pd.DataFrame:
    with open(log_path, 'r') as log:
        return log.read()

def evolution(log_info: pd.DataFrame):
    pass


if __name__ == "__main__":
    test_path = src_root() / 'test' / 'ece'
    log_path  = test_path / '1_preNPT' / 'bto.log'

    log_info = get_log_info(log_path)
    disp_re = r'<u>\s*=\s*(.*?)\s+(.*?)\s+(.*?)$'
    disp_matches: list[tuple[str, str, str]] = re.findall(disp_re, log_info, re.MULTILINE)
    disp_vectors = list(map(lambda dv: tuple(map(float, dv)), disp_matches))

    print(disp_vectors)
    print(len(disp_vectors))

from pathlib import Path
from typing import NamedTuple


class Runner(NamedTuple):
    sim_name: str
    working_dir: Path
    feram_path: Path

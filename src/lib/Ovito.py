import re
import numpy as np
import pandas as pd
from typing import Optional
from numpy.typing import NDArray
from pathlib import Path

from src.lib.Operations import *


def parse_dipo_df(fname: Path) -> pd.DataFrame:
    columns = ['x', 'y', 'z', 'ux', 'uy', 'uz']
    pd_df   = pd.read_table(fname, sep=r'\s+', header=None).iloc[:, 0:6]
    renamed = pd_df.rename(columns=dict(enumerate(columns)))
    return renamed


def parse_mod(fname: Path) -> NDArray:
    with open(fname, 'r') as fr:
        raw=fr.readlines()

    mod = np.array(
        list(filter(None,
                    map(lambda x: list(map(int, x.strip().split())), raw))))

    return mod


def vorticity3d(u: NDArray, v: NDArray, w: NDArray, dx: float, dy: float, dz: float) -> tuple[NDArray, NDArray, NDArray]:
    dudz, dudy, _    = np.array(np.gradient(u, dz, dy, dx))
    dvdz, _   , dvdx = np.array(np.gradient(v, dz, dy, dx))
    _   , dwdy, dwdx = np.array(np.gradient(w, dz, dy, dx))

    return (dwdy - dvdz, dudz - dwdx, dvdx - dudy)


def vorticity3d_df(dipo_df: pd.DataFrame, dx: float, dy: float, dz: float) -> pd.DataFrame:
    df = dipo_df.copy()

    Lx, Ly, Lz  = [int(df[e].max()) + 1 for e in ['x', 'y', 'z']]
    ux, uy, uz  = [df[f'u{e}'].to_numpy().reshape(Lz, Ly, Lx) for e in ['x', 'y', 'z']]
    vorticities = vorticity3d(ux, uy, uz, dx, dy, dz)

    df['vtx'], df['vty'], df['vtz'] = [v.reshape(Lx * Ly * Lz) for v in vorticities]

    return df


def write_dump(dump_path: Path, dipo_files: Sequence[Path], mod_file: Optional[Path]):
    modulation = parse_mod(mod_file)[:, 3] if mod_file else np.array([0])  # _xm, _ym, _zm, mm = mod[:,0], mod[:,1], mod[:,2], mod[:,3]
    atom_types = { t: i + 1 for i, t in enumerate(np.unique(modulation)) }

    with open(dump_path, 'w') as dump:
        for i, dump_path in enumerate(dipo_files):
            df = vorticity3d_df(parse_dipo_df(dump_path), dx = 1, dy = 1, dz = 1)

            x, y, z       = df.x, df.y, df.z
            ux, uy, uz    = df.ux, df.uy, df.uz
            vtx, vty, vtz = df.vtx, df.vty, df.vtz

            modulation2 = modulation if mod_file else np.repeat(0, len(x))
            n_atoms     = len(df)

            dump.write('ITEM: TIMESTEP\n'
                f'{i} {dump_path.name}\n'
                'ITEM: NUMBER OF ATOMS\n'
                f'{n_atoms}\n'
                'ITEM: BOX BOUNDS pp pp pp\n'
                f'0 {df.x.max() + 1}\n'
                f'0 {df.y.max() + 1}\n'
                f'0 {df.z.max() + 1}\n'
                'ITEM: ATOMS id type q xu yu zu mux muy muz vx vy vz\n'
            )
            for j in range(n_atoms):
                dump.write(f'{j + 1:d} {atom_types[modulation2[j]]:d} {modulation2[j]:d} '
                    f'{int(x[j]):d} {int(y[j]):d} {int(z[j]):d} '
                    f'{ux[j]:.6f} {uy[j]:.6f} {uz[j]:.6f} '
                    f'{vtx[j]:.6f} {vty[j]:.6f} {vtz[j]:.6f}\n'
                )


class WriteOvito(Operation):
    def __init__(self, file: FileOut, working_dir: DirIn, ext: str, mod_file: Optional[FileIn] = None) -> None:
        super().__init__(lambda: self.do(file, working_dir, ext, mod_file))

    @as_result(Exception)
    def safe_write(self, file: FileOut, dipo_files: Sequence[Path], mod_file: Optional[FileIn]):
        write_dump(file.path, dipo_files, mod_file.path if mod_file else None)

    def do(self, file: FileOut, working_dir: DirIn, ext: str, mod_file: Optional[FileIn]) -> OperationR:
        def natsort(file: Path) -> list[str | int]:
            return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', file.name)]

        dipo_files = sorted(working_dir.path.glob(f'*.{ext}'), key = natsort)
        # print(dipo_files)

        def dipo_files_exist(dipo_files: Sequence[Path]) -> Result[Sequence[Path], str]:
            if len(dipo_files) > 0:
                return Ok(dipo_files)
            else:
                return Err(f'No *.{ext} file found in {working_dir}')

        return do(
            Ok(res)
            for checked_dipos in dipo_files_exist(dipo_files)
            for checked_out   in file.check_preconditions()
            for checked_in    in (mod_file.check_preconditions() if mod_file else Ok(None))
            for res in self.safe_write(checked_out, checked_dipos, checked_in)
        ).map(lambda _: f'{type(self).__name__}: {file.path}').map_err(lambda x: f'{type(self).__name__}: {x}')

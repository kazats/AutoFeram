import argparse
import numpy as np
import pandas as pd
from collections.abc import Mapping
from numpy.typing import NDArray
from pathlib import Path


def parse_dipo_df(fname: Path) -> pd.DataFrame:
    columns = ['x', 'y', 'z', 'ux', 'uy', 'uz']
    pd_df   = pd.read_table(fname, sep=r'\s+', header=None).iloc[:, 0:6]
    renamed = pd_df.rename(columns=dict(enumerate(columns)))
    # return pl.from_pandas(pd_df)
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


def write_dump(file: Path, modulation: NDArray, atom_types: Mapping[NDArray, int]):
    with open(dump_file, 'w') as dump:
        for i, file in enumerate(dipo_files):
            print(file)

            df = vorticity3d_df(parse_dipo_df(file), dx = 1, dy = 1, dz = 1)

            x, y, z       = df.x, df.y, df.z
            ux, uy, uz    = df.ux, df.uy, df.uz
            vtx, vty, vtz = df.vtx, df.vty, df.vtz

            modulation2 = modulation if mod_file else np.repeat(0, len(x))
            n_atoms     = len(df)

            dump.write('ITEM: TIMESTEP\n'
                f'{i}\t{file}\n'
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Transform Feram output to dump format.')
    parser.add_argument('extension', metavar='ext', type=str, nargs=1,
                        help='file extension')
    parser.add_argument('-p', dest='path', type=str, default='./',
                        help='set working directory (default=./)')
    parser.add_argument('-s', dest='step_size', type=int, default=1,
                        help='select files by a certain step size (default=1)')
    parser.add_argument('-r', dest='reverse', action='store_true', default=False,
                        help='sort files in reverse order (default=False)')
    parser.add_argument('-m', dest='modulation', type=str, default=None,
                        help='[optional] add modulation information to dump file (default=None)')

    args     = parser.parse_args()
    ext      = args.extension[0]
    path     = Path(args.path)
    step     = args.step_size
    reverse  = args.reverse
    mod_file = args.modulation

    dump_file  = Path(f'dump_vtx_{ext}')
    dipo_files = sorted(path.glob(f'*.{ext}'), key=lambda f: int(f.stem), reverse=reverse)

    if len(dipo_files) == 0:
        print(f'[Warning] No *.{ext} file found!')
        exit()

    modulation = parse_mod(mod_file)[:, 3] if mod_file else np.array([0])  # _xm, _ym, _zm, mm = mod[:,0], mod[:,1], mod[:,2], mod[:,3]
    atom_types = { t: i + 1 for i, t in enumerate(np.unique(modulation)) }

    write_dump(dump_file, modulation, atom_types)

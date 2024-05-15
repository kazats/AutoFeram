# module load anaconda/2019
import argparse
import os, sys, glob
import numpy as np
import pandas as pd
import re

natsort = lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

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

args = parser.parse_args()
ext=args.extension[0]
path=args.path
step=args.step_size
reverse=args.reverse
f_mod=args.modulation

def parse_dipo_df(fname=None):
    with open(fname, 'r') as fr:
        raw = fr.readlines()
    dipo_list = [list(map(float,c)) for c in list(map(lambda line: line.strip().split()[:6], raw))]
    columns = 'x y z ux uy uz'.split()
    return pd.DataFrame(data=dipo_list, columns=columns)

def parse_mod(fname=None):
    with open(fname, 'r') as fr:
        raw=fr.readlines()
    mod = np.array(list(filter(None, map(lambda x: list(map(int, x.strip().split())), raw))))
    return mod

def vorticity3d(u, v, w, dx=1, dy=1, dz=1):
    dudz, dudy, dudx = np.array(np.gradient(u, dz, dy, dx))
    dvdz, dvdy, dvdx = np.array(np.gradient(v, dz, dy, dx))
    dwdz, dwdy, dwdx = np.array(np.gradient(w, dz, dy, dx))
    return dwdy-dvdz, dudz-dwdx, dvdx-dudy

def vorticity3d_df(dipo_df=None, dx=1, dy=1, dz=1):
    df = dipo_df.copy()
    Lx, Ly, Lz = [int(df[ax].max())+1 for ax in 'xyz']
    ux, uy, uz = [df['u{}'.format(ax)].to_numpy().reshape(Lz, Ly, Lx) for ax in 'xyz']
    vtx, vty, vtz = vorticity3d(ux, uy, uz, dx, dy, dz)
    df['vtx'], df['vty'], df['vtz'] = [_v.reshape(Lx*Ly*Lz) for _v in (vtx, vty, vtz)]
    return df

# main program
f_out='dump_vtx_{}'.format(ext)
# f_dipos=sorted(glob.glob(os.path.join(path, '*.'+ext)), reverse=reverse)[::step]
f_dipos = sorted(glob.glob(os.path.join(path, '*.'+ext)), key=natsort, reverse=reverse)
if len(f_dipos)==0:
    print('[Warning] No *.{} file found!'.format(ext))
    exit()

if f_mod!=None:
    mod=parse_mod(f_mod)
    xm, ym, zm, mm = mod[:,0], mod[:,1], mod[:,2], mod[:,3]
else:
    mm=[0]

Typ={}
for _i,_t in enumerate(np.unique(mm)):
    if _t not in Typ:
        Typ[_t]=_i+1

with open(f_out, 'w') as fw:
    for _i, _f in enumerate(f_dipos):
        print(_f)
        df = vorticity3d_df(dipo_df=parse_dipo_df(fname=_f), dx=1, dy=1, dz=1)
        x, y, z = df.x, df.y, df.z
        ux, uy, uz = df.ux, df.uy, df.uz
        vtx, vty, vtz = df.vtx, df.vty, df.vtz
        mm = mm if f_mod!=None else [0 for _ in range(len(x))]
        ncell=len(df.x)
        fw.write('ITEM: TIMESTEP\n')
        fw.write('%d\t%s\n'%(_i, _f))
        fw.write('ITEM: NUMBER OF ATOMS\n')
        fw.write('%d\n'%ncell)
        fw.write('ITEM: BOX BOUNDS pp pp pp\n')
        fw.write('0 %d\n'%(int(df.x.max())+1))
        fw.write('0 %d\n'%(int(df.y.max())+1))
        fw.write('0 %d\n'%(int(df.z.max())+1))
        fw.write('ITEM: ATOMS id type q xu yu zu mux muy muz vx vy vz\n')
        for _j in range(len(df.x)):
            fw.write('{:d} {:d} {:d} '.format(_j+1, Typ[mm[_j]], mm[_j]))
            fw.write('{:d} {:d} {:d} '.format(int(x[_j]), int(y[_j]), int(z[_j])))
            fw.write('{:.6f} {:.6f} {:.6f} '.format(ux[_j], uy[_j], uz[_j]))
            fw.write('{:.6f} {:.6f} {:.6f}\n'.format(vtx[_j], vty[_j], vtz[_j]))

print('FINISH: {}'.format(f_out))

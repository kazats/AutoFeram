from dataclasses import dataclass
import os
import numpy as np
import matplotlib.pylab as plt
#import seaborn as sns
import pandas as pd
import statistics
import math
import sys
import subprocess
import matplotlib as mat
import matplotlib.cm as cm
from matplotlib.ticker import NullFormatter
import materials
import pickle

markers = ['o', '*', '<', '3', 'v', '^', '>', '1', '2', '4', '8', 's', 'p', 'P', 'h', 'H', '+', 'x', 'X', 'D']
linestyles = ['-', '--', '-.', ':', 'solid', 'dashed', 'dashdot', 'dotted','-', '--', '-.', ':', 'solid', 'dashed', 'dashdot', 'dotted']
prop_cycle = plt.rcParams['axes.prop_cycle']
colors = prop_cycle.by_key()['color']

### math post processing
def mag(x):
    return math.sqrt(sum(i**2 for i in x))

def project_u_onto_v(U, V):
    u = np.array(U)   # vector u
    v = np.array(V)   # vector v:
    #v_norm = np.sqrt(sum(v**2))
    return (np.dot(u, v)/np.dot(v,v))*v

### analysis
def determine_phase(Px, Py, Pz):
    zero_noise=0.5
    px=abs(Px)
    py=abs(Py)
    pz=abs(Pz)
    phasename=''
    if (px>zero_noise and py>zero_noise and pz>zero_noise):
        if (abs(px-py)<zero_noise*1 and abs(px-pz)<zero_noise*1):
            phasename='R' #(a,a,a)
        elif ((abs(px-py)<zero_noise*1 and abs(px-pz)>zero_noise*1 and px<pz) or (abs(px-pz)<zero_noise*1 and abs(px-py)>zero_noise*1 and px<py) or (abs(pz-py)<zero_noise*1 and abs(pz-px)>zero_noise*1 and pz<px)):
            phasename='Ma' #(a,a,b), a<b
        elif ((abs(px-py)<zero_noise*1 and abs(px-pz)>zero_noise*1 and px>pz) or (abs(px-pz)<zero_noise*1 and abs(px-py)>zero_noise*1 and px>py) or (abs(pz-py)<zero_noise*1 and abs(pz-px)>zero_noise*1 and pz>px)):
            phasename='Mb' #(a,a,b), a>b
        else:
            phasename='M (111)' #(a,b,c)
    elif ((px<zero_noise and py>zero_noise and pz>zero_noise and abs(py-pz)<zero_noise*1) or (px>zero_noise and py<zero_noise and pz>zero_noise and abs(px-pz)<zero_noise*1) or (px>zero_noise and py>zero_noise and pz<zero_noise and abs(py-px)<zero_noise*1)):
        phasename='O' #(a,a,0)
    elif ((px<zero_noise and py>zero_noise and pz>zero_noise and abs(py-pz)>zero_noise*1) or (px>zero_noise and py<zero_noise and pz>zero_noise and abs(px-pz)>zero_noise*1) or (px>zero_noise and py>zero_noise and pz<zero_noise and abs(py-px)>zero_noise*1)):
        phasename='Mc' #(a,b,0)
    elif ((px<zero_noise and py<zero_noise and pz>zero_noise) or (px>zero_noise and py<zero_noise and pz<zero_noise) or (px<0.5 and py>0.5 and pz<0.5)):
        phasename='T' #(a,0,0)
    elif ((px<zero_noise and py<zero_noise and pz<zero_noise)):
        phasename='C' #(0,0,0)
    else:
        phasename='M'
    return phasename

### file post processing
def get_avg(path, zstar, avgfile="thermo.avg",comment="thermo"):
    ''' this save avg file in df and .csv format '''
    data = open(f"{path}/{avgfile}", "r").readlines()
    factor = get_factor(zstar)
    #ex,ey,ez,px,py,pz,T, totalP, Edk, dkt, Eak =[],[],[],[],[],[],[], [], [], [], []
    ex,ey,ez,px,py,pz,T, totalP,phase, Edk, dkt, Eak,Etot,EdE =[],[],[],[],[],[],[],[],[],[],[],[],[],[]
    E_dipolekinetic, E_longrange, E_dipolefield, E_self, E_homostrain, E_homocoupling, E_inhostrain, E_inhocoupling, E_tot, E_thermostat, E_acoukinetic, E_shortrange, E_inhomodulation  = [], [], [], [], [], [], [], [], [], [], [], [], []
    s_xx, s_yy, s_zz, s_yz, s_xz, s_xy = [],[],[],[],[],[]
    u_1, u_2, u_3 = [], [], []
    uu1, uu2, uu3, uu4, uu5, uu6 = [],[],[],[],[],[] 
    p_1, p_2, p_3 = [],[],[]  
    pp1, pp2, pp3, pp4, pp5, pp6 = [],[],[],[],[],[] 
    for d in data:
        d=d.split(' ') #type of d: list
        d=filter(None, d) #type of d:filter
        d=[float(i) for i in d]
        T.insert(0,int(d[0]))
        ex.insert(0,float(d[1])) #electric field
        ey.insert(0,float(d[2]))
        ez.insert(0,float(d[3]))
        s_xx.insert(0,float(d[4]))
        s_yy.insert(0,float(d[5]))
        s_zz.insert(0,float(d[6]))
        s_yz.insert(0,float(d[7]))
        s_xz.insert(0,float(d[8]))
        s_xy.insert(0,float(d[9]))
        u_1.insert(0,float(d[10]))
        u_2.insert(0,float(d[11]))
        u_3.insert(0,float(d[12]))
        uu1.insert(0,float(d[13]))
        uu2.insert(0,float(d[14]))
        uu3.insert(0,float(d[15]))
        uu4.insert(0,float(d[16]))
        uu5.insert(0,float(d[17]))
        uu6.insert(0,float(d[18]))
        E_dipolekinetic.insert(0,float(d[19]))  
        E_longrange.insert(0,float(d[20]))     
        E_dipolefield.insert(0,float(d[21]))         
        E_self.insert(0,float(d[22]))            
        E_homostrain.insert(0,float(d[23]))         
        E_homocoupling.insert(0,float(d[24]))               
        E_inhostrain.insert(0,float(d[25]))          
        E_inhocoupling.insert(0,float(d[26]))                  
        E_tot.insert(0,float(d[27]))             
        E_thermostat.insert(0,float(d[28]))            
        E_acoukinetic.insert(0,float(d[31]))            
        E_shortrange.insert(0,float(d[32]))          
        E_inhomodulation.insert(0,float(d[33]))          
        p_1.insert(0,float(d[34]))
        p_2.insert(0,float(d[35]))
        p_3.insert(0,float(d[36]))
        pp1.insert(0,float(d[37]))
        pp2.insert(0,float(d[38]))
        pp3.insert(0,float(d[39]))
        pp4.insert(0,float(d[40]))
        pp5.insert(0,float(d[41]))
        pp6.insert(0,float(d[42]))

        px.insert(0,float(d[10])*factor) #polarization
        py.insert(0,float(d[11])*factor)
        pz.insert(0,float(d[12])*factor)
        totalP.insert(0,float(np.sqrt(d[10]*factor*d[10]*factor + d[11]*factor*d[11]*factor + d[12]*factor*d[12]*factor)))
        phase.insert(0,determinephase(float(d[10])*factor, float(d[11])*factor, float(d[12])*factor))

        # below is arcsin: value: 0-90-0
        #anglebetweenEfield.insert(0,180/np.pi*np.arcsin(mag(np.cross([d[1],d[2],d[3]], [d[10],d[11],d[12]]))/(mag([d[1],d[2],d[3]])*(mag([d[10],d[11],d[12]])))))
        # below is arccos: value: 0-180
        #anglebetweenEfield.insert(0,180/np.pi*np.arccos( (d[1] * d[10] + d[2] * d[11] + d[3] * d[12]) / (np.sqrt(d[1]*d[1] + d[2]*d[2] + d[3]*d[3]) * np.sqrt(d[10]*d[10] + d[11]*d[11] + d[12]*d[12])) ))
        # angle = arccos[(xa * xb + ya * yb + za * zb) / (√(xa2 + ya2 + za2) * √(xb2 + yb2 + zb2))]
        # [d[1], d[2], d[3]] = [ex, ey, ez] - [xa, ya, za]
        # [d[10], d[11], d[12]] = [px, py, pz] - [xb, yb, zb]

        #anglebetweenXaxis.insert(0,180/np.pi*np.arccos( (1 * d[10] + 0 * d[11] + 0 * d[12]) / (np.sqrt(1*1 + 0*0 + 0*0) * np.sqrt(d[10]*d[10] + d[11]*d[11] + d[12]*d[12])) ))

        #Edk.insert(0,float(d[19]))
        #dkt.insert(0,float(d[30]))
        #Eak.insert(0,float(d[31]))
        #Etot.insert(0,float(d[27]))
        #EdE.insert(0,float(d[21]))

#    d=np.array(list(zip(T,ex,ey,ez,px,py,pz, totalP, Edk, dkt, Eak)))
#    df = pd.DataFrame(d, columns="T ex ey ez px py pz P Edk dkt Eak".split(" "))
#    d=np.array(list(zip(T, px,py,pz, totalP, phase))) # conversion into np.array deletes the type info.
    d=list(zip(T, ex,ey,ez, px,py,pz, totalP, phase, E_dipolekinetic, E_longrange, E_dipolefield, E_self, E_homostrain, E_homocoupling, E_inhostrain, E_inhocoupling, E_tot, E_thermostat, E_acoukinetic, E_shortrange, E_inhomodulation, s_xx, s_yy, s_zz, s_yz, s_xz, s_xy, u_1, u_2, u_3, uu1, uu2, uu3, uu4, uu5, uu6, p_1, p_2, p_3, pp1, pp2, pp3, pp4, pp5, pp6   ))
    
    df = pd.DataFrame(d, columns="T ex ey ez px py pz P phase E_dipolekinetic E_longrange E_dipolefield E_self E_homostrain E_homocoupling E_inhostrain E_inhocoupling E_tot E_thermostat E_acoukinetic E_shortrange E_inhomodulation s_xx s_yy s_zz s_yz s_xz s_xy u_1 u_2 u_3 uu1 uu2 uu3 uu4 uu5 uu6 p_1 p_2 p_3 pp1 pp2 pp3 pp4 pp5 pp6".split(" ")) 
    df.to_csv(f"{path}/{comment}.csv")
    return df

def get_hl(path,name, zstar, extract=False):
    if extract == False and os.path.exists(f'{path}/{name}_hl.txt'):
        return pd.read_csv(f'{path}/{name}_hl.txt', header=0, index_col=0)
    else:
        data=open(f'{path}/{name}.hl','r').readlines()
        T, Etot,Ex,Ey,Ez,s1,s2,s3,s4,s5,s6,u1,u2,u3,p1,p2,p3,ptot,Ek=[],[],[], [],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]
        factor=get_factor(zstar)
        for d in data:
            d=[float(i) for i in d.split()]
            T.append(float(d[1]))
            Ex.append(float(d[2]))
            Ey.append(float(d[3]))
            Ez.append(float(d[4]))
            Etot.append(np.linalg.norm([float(d[2]),float(d[3]),float(d[4])]))
    #         E_project_100.append( project_u_onto_v([float(d[2]), float(d[3]), float(d[4])], [1,0,0]) )
            s1.append(float(d[5]))
            s2.append(float(d[6]))
            s3.append(float(d[7]))
            s4.append(float(d[8]))
            s5.append(float(d[9]))
            s6.append(float(d[10]))
            u1.append(float(d[11]))
            u2.append(float(d[12]))
            u3.append(float(d[13]))
            p1.append(float(d[11])*factor) #displacement * factor = polarization
            p2.append(float(d[12])*factor)
            p3.append(float(d[13])*factor)
    #         P_project_100.append( project_u_onto_v([float(d[11])*factor, float(d[12])*factor, float(d[13])*factor], [1,0,0]) )
            ptot.append(np.linalg.norm([float(d[11])*factor,float(d[12])*factor,float(d[13])*factor]))
            Ek.append(float(d[20]))
        d=list(zip(T,Ex,Ey,Ez,Etot, s1,s2,s3,s4,s5,s6,p1,p2,p3,ptot,Ek))
        df = pd.DataFrame(d, columns="T Ex Ey Ez Etot s1 s2 s3 s4 s5 s6 px py pz ptot Ek".split(" "))
        df.to_csv(f'{path}/{name}_hl.txt')
        return df

def get_from_coord(path,name,zstar):
    data=open(f'{path}/{name}','r').readlines()
    x,y,z,u1,u2,u3,p1,p2,p3,ptot=[],[],[],[],[],[],[],[],[],[]
    factor=get_factor(zstar)
    for d in data:
        d=d.split(' ')
        d=filter(None, d)
        d=[float(i) for i in d]
        x.append(float(d[0]))
        y.append(float(d[1]))
        z.append(float(d[2]))
        u1.append(float(d[3]))
        u2.append(float(d[4]))
        u3.append(float(d[5]))
        p1.append(float(d[3])*factor) #displacement * factor = polarization
        p2.append(float(d[4])*factor)
        p3.append(float(d[5])*factor)
        ptot.append(np.linalg.norm([float(d[3])*factor,float(d[4])*factor,float(d[5])*factor]))
    d=list(zip(x,y,z,p1,p2,p3,ptot))
    df = pd.DataFrame(d, columns="x y z px py pz ptot".split(" "))
#     df.to_csv(f"{path}/{name}_hl.csv")
    return df

def get_p(path, name, zstar):
    data=open(f'{path}/{name}.dipoRavg','r').readlines()
    p1,p2,p3=[],[],[]
    factor=get_factor(zstar)
    for d in data:
        d=d.split(' ')
        d=filter(None, d)
        d=[float(i) for i in d]
        p1.append(float(d[3])*factor) #displacement * factor = polarization
        p2.append(float(d[4])*factor)
        p3.append(float(d[5])*factor)
    return p1,p2,p3

def polarization_distribution(path,name,zstar,setting=[('px','r'),('py','g'),('pz','b')]): # .coord, .restart
    d=get_from_coord(path=f'{path}',name=f'{name}', zstar=zstar)
    for i in range(len(setting)):
        n, bins, patches = plt.hist(x=d[setting[i][0]], bins='auto', density=True,color=setting[i][1],alpha=0.5, rwidth=1)

### forget what's for
def get_properties_from_txt(file):
    data=open(f'{file}','r').readlines()
    p=[]

    for d in data:
        d=[float(i.replace(' ', '')) for i in d.split()]
        p.append(float(d[0])) #displacement * factor = polarization
    return p

def layerP_fromdipoRavg(Dname,fname,zstar):
    data = open(f"{Dname}/{fname}.dipoRavg", "r").readlines()
    factor=get_factor(zstar)
    x,y,z,px,py,pz =[],[],[],[],[],[]
    for d in data:
        d=d.split(' ') #type of d: list
        d=filter(None, d) #type of d:filter
        d=[float(i) for i in d]
        x.append(float(d[0])*factor) #polarization
        y.append(float(d[1])*factor)
        z.append(float(d[2])*factor)
        #pxpypz.append([float(d[3])*factor,float(d[4])*factor,float(d[5])*factor])
        px.append(float(d[3])*factor) #polarization
        py.append(float(d[4])*factor)
        pz.append(float(d[5])*factor)
    d=list(zip(x,y,z,px,py,pz))
    df = pd.DataFrame(d, columns="x y z px py pz".split(" "))
    df.to_csv(f"{Dname}/layerx_dipoRavg.csv")
    return df

def evolution(path, name, zstar, firsttime=False,inittime=-160):
    factor=get_factor(zstar)
    if firsttime==True and os.path.exists(f'{path}/{name}.log'):
        shell(f"grep -a '<u>' {path}/{name}.log | awk '{{print $3 \"\\t\" $4 \"\\t\" $5}}' > {path}/displacement_u.txt")
        shell(f"grep -a total_energy {path}/{name}.log | awk '{{print $2}}' > {path}/total_energy.txt")
        shell(f"grep -a dipo_kinetic {path}/{name}.log | awk '{{print $2}}' > {path}/dipo_kinetic.txt")
    df_u = pd.read_csv(f'{path}/displacement_u.txt', sep="\t", header=None, names=['px', 'py', 'pz'],index_col=False)
    df_p = df_u * factor
    df_Etot=pd.read_csv(f'{path}/total_energy.txt',header=None, names=['Etot'],index_col=False)
    df_Edk=pd.read_csv(f'{path}/dipo_kinetic.txt',header=None, names=['Edk'],index_col=False)
    df_T = df_Edk.rename(columns={'Edk': 'kelvin'}) / (1.5*8.617E-5)
#     df_Etot = pd.DataFrame(Etot, columns =['total_energy'])
#     df_Edk = pd.DataFrame(Edk, columns =['dipo_kinetic'])
    df_0 = df_Etot.merge(df_Edk, left_index=True,right_index=True)
    df = df_0.merge(df_T, left_index=True,right_index=True)

    timestep = shell(f"grep dt {path}/{name}.feram  | awk '{{print $3}}'")
    if name == 'preNPT':
        initial_time=inittime #-160
        initial_time_u=inittime #-160 #-40
    elif name == 'preNPE':
        initial_time=0
        initial_time_u=0 #80
    elif name == 'rampNPE':
        print('Please use another function: evolution_ramping')
    elif name == 'postNPE':
        initial_time=220
        initial_time_u=220 #300
    else:
        initial_time=-10000000
        initial_time_u=-10000000

    df.insert(0, "time_ps", [round(i * float(timestep) + initial_time,3) for i in list(range(0,len(df)))])
    df = df[:-1]

    df_p.insert(0, "time_ps", [round(i * float(timestep) + initial_time_u,3) for i in list(range(0,len(df_p)))])
    df_final = df.merge(df_p, on="time_ps", how = 'outer')
    return df_final

def evolution_ramping(path, name, zstar, firsttime=False,inittime=-160):
    factor=get_factor(zstar)
    if firsttime==True and os.path.exists(f'{path}/{name}.hl'):
        shell(f"awk '{{print $1 \"\\t\" $2 \"\\t\" $3 \"\\t\" $4 \"\\t\" $5 \"\\t\" $12 \"\\t\" $13 \"\\t\" $14 \"\\t\" $21 \"\\t\" $24 \"\\t\" $31}}' {path}/{name}.hl > {path}/simplified_hl.txt")
    df = pd.read_csv(f'{path}/simplified_hl.txt', sep="\t", header=None,index_col=False, names=['step','kelvin','Ex','Ey','Ez','Ux','Uy','Uz','Edk','dipole_E_field','Etot'])
    df['px']=df['Ux']*factor
    df['py']=df['Uy']*factor
    df['pz']=df['Uz']*factor
    L = shell(f"grep L {path}/{name}.feram  | awk '{{print $3}}'")
    df['Edk']=df['Edk']/(int(L)*int(L)*int(L))
    df['kelvin']=df['Edk']/(1.5*8.617E-5)
    df['Etot']=df['Etot']/(int(L)*int(L)*int(L))
    timestep = shell(f"grep dt {path}/{name}.feram  | awk '{{print $3}}'")
    n_hl_f = shell(f"grep n_hl_freq {path}/{name}.feram  | awk '{{print $3}}'")
    if n_hl_f == []:
        n_hl_f = [10000] #This is the default value, specified in source code
    initial_time=120 #ps
    df.insert(0, "time_ps", [round((i+1) * float(timestep) * int(n_hl_f) + initial_time,3) for i in list(range(0,len(df)))])
    return df


def gen_path(d, step, name, path):
    return f'{path}/{d}/{step}{name}'


def gen_evo(f, step, path, name, ds, first, inittime):
    return {d: f(gen_path(d, step, name, path), name, first, inittime) for d in ds}
    #es = map(lambda d: f(gen_path(d, step), name, first), ds)
    #return dict(zip(ds, es))


def gen_evos(step_def, directories, path='.', first=False, inittime=-160):
    return {k: gen_evo(f, k, path, name, directories, first, inittime) for k, (name, f) in step_def.items()}


# def properties_evolution(des, directories, properties, abso=False, legend=True, colors=['b','cyan','black','green','pink','brown','orange','red','indigo','darkkhaki','fuchsia','skyblue','tomato','aquamarine']):
#     fig, (ax1) = plt.subplots(ncols=1, nrows=1, figsize=(8,5), tight_layout=True)
#     if abso==True:
#         if legend==True:
#             return [ax1.plot(des[step_num][dircs]['time_ps'],np.abs(des[step_num][dircs][properties]), color=colrs, linewidth=2, label=dircs) for (dircs, colrs) in zip(directories, colors[0:len(directories)]) for step_num in [1]]  ;
#             [ax1.plot(des[step_num][dircs]['time_ps'],np.abs(des[step_num][dircs][properties]), color=colrs, linewidth=2) for (dircs, colrs) in zip(directories, colors[0:len(directories)]) for step_num in [2,3,4]]
#         else:
#             return [ax1.plot(des[step_num][dircs]['time_ps'],np.abs(des[step_num][dircs][properties]), color=colrs, linewidth=2) for (dircs, colrs) in zip(directories, colors[0:len(directories)]) for step_num in [1,2,3,4]]
#     else:
#         if legend==True:
#             return [ax1.plot(des[step_num][dircs]['time_ps'],(des[step_num][dircs][properties]), color=colrs, linewidth=2, label=dircs) for (dircs, colrs) in zip(directories, colors[0:len(directories)]) for step_num in [1]] ;
#             return [ax1.plot(des[step_num][dircs]['time_ps'],(des[step_num][dircs][properties]), color=colrs, linewidth=2) for (dircs, colrs) in zip(directories, colors[0:len(directories)]) for step_num in [2,3,4]]
#         else:
#             return [ax1.plot(des[step_num][dircs]['time_ps'],(des[step_num][dircs][properties]), color=colrs, linewidth=2) for (dircs, colrs) in zip(directories, colors[0:len(directories)]) for step_num in [1,2,3,4]]
#     return True

def temperature_diff(des, directories):
    print("Temperature differences:\n")
    [print(statistics.mean([float(i) for i in des[4][dire]['kelvin'][130000:179999]]) - statistics.mean([float(i) for i in des[2][dire]['kelvin'][100000:119999]])) for dire in directories]
    return True

def temperature_diff_rescaled(des, directories):
    print("Temperature differences:\n")
    print([((statistics.mean([float(i) for i in des[4][dire]['kelvin'][130000:179999]]) - statistics.mean([float(i) for i in des[2][dire]['kelvin'][100000:119999]]))/5) for dire in directories])
    print('\n\n---------average temp. of 2preNPE----------\n')
    print([(round(statistics.mean([float(i) for i in des[2][dire]['kelvin'][100000:119999]]),2)) for dire in directories])
    print('\n\n---------average temp. of 4postNPE----------\n')
    print([(round(statistics.mean([float(i) for i in des[4][dire]['kelvin'][130000:179999]]),2)) for dire in directories])
    return [((statistics.mean([float(i) for i in des[4][dire]['kelvin'][130000:179999]]) - statistics.mean([float(i) for i in des[2][dire]['kelvin'][100000:119999]]))/5) for dire in directories] , [(round(statistics.mean([float(i) for i in des[2][dire]['kelvin'][100000:119999]]),2)) for dire in directories]

def phase_evolution(A, d):
#     A='T128'; d=des
    print(A,': ',determinephase( sum(d[2][A]['px'][100000:119999])/len(d[2][A]['px'][100000:119999]),
                            sum(d[2][A]['py'][100000:119999])/len(d[2][A]['py'][100000:119999]),
                            sum(d[2][A]['pz'][100000:119999])/len(d[2][A]['pz'][100000:119999])) ,' -> ',
      determinephase( sum(d[4][A]['px'][130000:179999])/len(d[4][A]['px'][130000:179999]),
                    sum(d[4][A]['py'][130000:179999])/len(d[4][A]['py'][130000:179999]),
                    sum(d[4][A]['pz'][130000:179999])/len(d[4][A]['pz'][130000:179999])) )
    return [ A, sum(d[2][A]['px'][100000:119999])/len(d[2][A]['px'][100000:119999]), sum(d[2][A]['py'][100000:119999])/len(d[2][A]['py'][100000:119999]),sum(d[2][A]['pz'][100000:119999])/len(d[2][A]['pz'][100000:119999]), '---->', sum(d[4][A]['px'][130000:179999])/len(d[4][A]['px'][130000:179999]), sum(d[4][A]['py'][130000:179999])/len(d[4][A]['py'][130000:179999]), sum(d[4][A]['pz'][130000:179999])/len(d[4][A]['pz'][130000:179999]) ]


def generate_frozen_dipole(size,ratio,zstar,p1,p2,path='./'):
    factor=get_factor(zstar)
    print(f'ratio = {ratio}')
    px1,py1,pz1=p1
    px2,py2,pz2=p2
    px ,py ,pz  = px1+(px2-px1)*ratio,py1+(py2-py1)*ratio,pz1+(pz2-pz1)*ratio
    ux = px/factor
    uy = py/factor
    uz = pz/factor
    print(px,py,pz)
    for i in range(0,size):
        for k in range(0,size):
            for j in range(0,size):
                original_stdout = sys.stdout # Save a reference to the original standard output
                with open(f'{path}/bto.defects', 'a') as f:
                    sys.stdout = f # Change the standard output to the file we created.
                    print(f"{i} {j} {k} {ux} {uy} {uz}")
                    sys.stdout = original_stdout # Reset the standard output to its original value

                    
                    
def save_dict_to_pkl(dic, pklfilename):
    # save dictionary to person_data.pkl file
    with open(f'{pklfilename}.pkl', 'wb') as fp:
        pickle.dump(dic, fp)
        print('dictionary saved successfully to file')
        
def read_pkl_to_dict(pklfilename):
    dic = {}
    with open(f'{pklfilename}', 'rb') as fp:
        dic = pickle.load(fp)
    return dic
    
def tempevolution_coord(path, Tstart, Tend, dT, pklname, zstar, coordprename=''):
    name = [coordprename+str(T)+'.coord' for T in range(Tstart,Tend+1, dT)]
    dict_temp_pxpypz = {}
    for T,n in zip(range(Tstart,Tend+1, dT),name):
        dict_temp_pxpypz[T] = get_from_coord(path, n, zstar)
    # temps = []; names = []; dict(zip(temps, map(lambda n: get_from_coord(path, n), names)) : same as the above two lines
    save_dict_to_pkl(dict_temp_pxpypz, pklname)
    return dict_temp_pxpypz

def tempevolution_dipoRavg(path, Tstart, Tend, dT, pklname, zstar, dipoRavgprename=''):
    name = [dipoRavgprename+str(T)+'.dipoRavg' for T in range(Tstart,Tend+1, dT)]
    dict_temp_pxpypz = {}
    for T,n in zip(range(Tstart,Tend+1, dT),name):
        dict_temp_pxpypz[T] = get_from_coord(path, n,zstar)
    # temps = []; names = []; dict(zip(temps, map(lambda n: get_from_coord(path, n), names)) : same as the above two lines
    save_dict_to_pkl(dict_temp_pxpypz, pklname)
    return dict_temp_pxpypz

def hist2D_polarization(data_dict, T,cb_min, cb_max, lim_1, lim_2, colormap='afmhot_r',P1='px', P2='py', title='',cbarmap=False, bin_n='auto', axislabel=False):
    x = data_dict[T][P1] # data_dict: from tempevolution_coord
    y = data_dict[T][P2]
 
    fig, ax = plt.subplots(figsize=(4,4)) #, layout='tight'
    cmap_reversed = mat.cm.get_cmap(colormap)
    h = ax.hist2d(x, y, bins=bin_n, cmap=cmap_reversed, vmin=cb_min, vmax=cb_max)
    if cbarmap == True:
        cbar = fig.colorbar(h[3],ax=ax)
        cbar.ax.set_ylabel('Counts')
    ax.axhline(0, color='k', alpha=0.5)
    ax.axvline(0, color='k', alpha=0.5)

    if axislabel == True:
        ax.set_xlabel(P1)
        ax.set_ylabel(P2)
        ax.set_title(title)
    if axislabel == False:
        plt.tick_params(
            axis='both',          # changes apply to the x-axis
            which='both',      # both major and minor ticks are affected
            labelbottom=False,      # ticks along the bottom edge are off
            labeltop=False,         # ticks along the top edge are off
            labelleft=False, 
            labelright=False)
        
    ax.set_xlim(lim_1, lim_2)
    ax.set_ylim(lim_1, lim_2)
    plt.savefig(f'{title}.pdf', bbox_inches="tight")
    return fig, ax

def hist2D_hist1D(data_dict, T, lim1, lim2, cb_min, cb_max, binx='auto', biny='auto',bin2d='auto',P1='px', P2='py', title='', colormap='afmhot_r', figx=6, figy=4):
    plt.clf()
    x = data_dict[T][P1] # data_dict: from tempevolution_coord
    y = data_dict[T][P2]

    nullfmt = NullFormatter()         # no labels
    # definitions for the axes
    left, width = 0.1, 0.65
    bottom, height = 0.1, 0.65
    bottom_h = left_h = left + width + 0.02   
    rect_hist2d = [left, bottom, width, height]
    rect_histx = [left, bottom_h, width, 0.2]
    rect_histy = [left_h, bottom, 0.2, height]

    fig,ax = plt.subplots(figsize=(figx, figy))
    fig.clf()

    axHist2D = plt.axes(rect_hist2d)
    axHistx = plt.axes(rect_histx)
    axHisty = plt.axes(rect_histy)
    axHistx.xaxis.set_major_formatter(nullfmt)
    axHisty.yaxis.set_major_formatter(nullfmt)
    axHisty.xaxis.tick_top()

    cmap_reversed = mat.cm.get_cmap(colormap)
    
    # setting=[('px','r'),('py','g'),('pz','b')]
    axHistx.hist(x=x, bins=binx, density=True,color='black',alpha=1, rwidth=1)
    axHisty.hist(x=y, bins=biny, density=True,color='black',alpha=1, rwidth=1, orientation='horizontal')
    h = axHist2D.hist2d(x, y, bins=bin2d, cmap=cmap_reversed, vmin=cb_min, vmax=cb_max)    
    cbar = fig.colorbar(h[3],ax=axHisty, location='right')
    cbar.ax.set_ylabel('Counts')

    axHist2D.axhline(0, color='black')
    axHist2D.axvline(0, color='black')
    axHistx.set_title(title)
    axHist2D.set_xlabel(P1)
    axHist2D.set_ylabel(P2)
    axHist2D.set_xlim(lim1, lim2)
    axHist2D.set_ylim(lim1, lim2)
    axHistx.set_xlim(axHist2D.get_xlim())
    axHisty.set_ylim(axHist2D.get_ylim())
    plt.savefig(f'{title}.pdf', bbox_inches="tight")
    return fig, ax

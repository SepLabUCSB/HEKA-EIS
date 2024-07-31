import numpy as np
from io import StringIO
import matplotlib.pyplot as plt
import scipy.io

plt.style.use('Z:\Projects\Miguel\Spyder\style.mplstyle')

# file = r'C:/Users/miguelorozco/Desktop/test.asc'
# file = r'C:/Users/miguelorozco/Desktop/3cycles_5k.asc'
file = r'D:\Miguel\20240729_EIS_Pt_microelectrode25.asc'
SAMPLE_FREQUENCY = 40000


def read_heka_data(file):
    '''
    Parse PATCHMASTER-output csv files.
    
    Use StringIO to parse through file (fastest method I've found)
    Convert only floats to np arrays
    '''
    if file == 'MEAS_ABORT':
        return 0,0,0
    
    if file.endswith('.mat'):
        return extract_matlab_iv_data(file)
    
    def isFloat(x):
        try: 
            float(x)
            return True
        except: 
            return False
    
    s = StringIO()
    with open(file, 'r') as f:
        for line in f:
            if isFloat(line.split(',')[0]):
                # Check for index number
                s.write(line)
    if s.getvalue() != '':
        s.seek(0)
        array = np.genfromtxt(s, delimiter=',')
        array = array.T
        _, t, i, _, v = array
        return t, v, i

def extract_matlab_iv_data(file):
    '''
    Extracts I-V type data from a PATHCMASTER-generated .mat file.
    Assumes Trace 1 in PATCHMASTER is I (Current)
    Assumes Trace 2 in PATCHMASTER is V (Voltage)
    
    Returns times, voltages, currents
    
    Exporting binary .mat files from PATCHMASTER is much, much faster
    than exporting as csv files    
    '''
    d = scipy.io.loadmat(file)
    
    
    sweeps = []
    traces = []
    for key in d.keys():
        if not key.startswith('Trace'):
            continue
        a,b,c, sweep, trace = key.split('_')
        sweeps.append(int(sweep))
        traces.append(int(trace))
        
    sweeps = list(set(sweeps))
    traces = list(set(traces))
    
    T = np.array([])
    V = np.array([])
    I = np.array([])
    
    for sweep in sweeps:
        for trace in traces:
            key = f'{a}_{b}_{c}_{sweep}_{trace}'
            arr = d[key]                         # [ [t1, v1], [t2, v2], ...]
            arr = arr.transpose()                # [ [t1, t2, ...], [v1, v2, ...] ]
            ts, vals = arr
            if trace == traces[0]:
                T = np.append(T,ts)
            if trace == 1:
                I = np.append(I, vals)
            elif trace == 2:
                V = np.append(V, vals)
                
    return T, V, I    
    

T, V, I = read_heka_data(file)

ft_V  = np.fft.rfft(V)[1:]
ft_I  = np.fft.rfft(I)[1:]
freqs = SAMPLE_FREQUENCY*np.fft.rfftfreq(len(V))[1:]

fig, ax = plt.subplots(dpi=300, figsize=(5,5))
ax.plot(freqs, abs(ft_V), 'o')
ax.set_xscale('log')
plt.xlabel('Frequency/ Hz')
plt.ylabel('FT Voltage')

'''
Removing the extra data points/frequencies!
'''
ft_I  = ft_I[abs(ft_V) > 5]
freqs = freqs[abs(ft_V) > 5]
ft_V  = ft_V[abs(ft_V) > 5]

Z = ft_V/ft_I #impedence

ax.plot(freqs, abs(ft_V), 'o', color='r')
# for i, j in zip(freqs, abs(ft_V)):
#    plt.text(i+np.log(i), j+1, '({}, {})'.format(round(i,1), round(j,1)),
#             fontsize=5)

fig, ax2 = plt.subplots(dpi=300, figsize=(5,5))
ax2.plot(np.real(Z), -np.imag(Z), 'o')
plt.xlabel(r"Z '")
plt.ylabel(r"- Z ''")
# plt.xlim(0,1E7)
# plt.ylim(0,1E7)


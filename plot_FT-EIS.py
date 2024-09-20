import numpy as np
from io import StringIO
import scipy.io
from matplotlib import pyplot as plt, cm, colors, animation as animation

plt.style.use('Z:\Projects\Miguel\Spyder\style.mplstyle')

# file = r'C:/Users/miguelorozco/Desktop/test.asc'
# file = r'C:/Users/miguelorozco/Desktop/3cycles_5k.asc'
# file = r'D:\Miguel\20240731\20240731_EIS_Pt_microelectrode1.asc'
# file = r'D:\Miguel\20240801\20240801_dummy_cell_troubleshooting1.asc'
# file = r'D:\Miguel\20240801\20240801_Pt_microelectrode1.asc'
# file = r'D:\Miguel\20240801\20240801_Pt_microelectrode_full_sweep.mat'
# file = r'D:\Miguel\20240805\20240805_Pt_microelectrode_EIS_1sweep_-700mV.asc'
# file = r'D:\Miguel\20240805\20240805_Pt_microelectrode_50_cycles_-0_7V.mat'
# file = r'D:\Miguel\20240805\20240805_Pt_microelectrode_CV_-200to-1000mV.asc'
# file = r'D:\Miguel\20240805\20240805_Pt_microelectrode_CV_-200to-700mV.asc'
file = r'D:\SECM\Data\20240905\20240905.asc'

SAMPLE_FREQUENCY = 10000
highest_freq_from_gen = 1000 # Hz

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
    
    sweeps = []
    s = StringIO()
    with open(file, 'r') as f:
        for line in f:
            if isFloat(line.split(',')[0]):
                # Check for index number
                s.write(line)
            if line.startswith('Sweep'):
                # print(line)
                # print(line.split(','))
                sweep_text = line.split(',')
                sweep_text = sweep_text[0].split('_')
                # print(sweep_text)
                sweeps.append(int(sweep_text[-1]))
    
    if s.getvalue() != '':
        s.seek(0)
        array = np.genfromtxt(s, delimiter=',')
        array = array.T
        _, t, i, _, v = array
    
    return t, v, i, sweeps

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
            arr = d[key]           # [ [t1, v1], [t2, v2], ...]
            arr = arr.transpose()  # [ [t1, t2, ...], [v1, v2, ...] ]
            ts, vals = arr
            if trace == traces[0]:
                T = np.append(T,ts)
            if trace == 1:
                I = np.append(I, vals)
            elif trace == 2:
                V = np.append(V, vals)
                
    return T, V, I, sweeps
    
def get_units(val):
    max_val = max(abs(val))
    
    if max_val <= 1E-16:
        return ('f', 1E-15)
    
    if max_val > 1E-16 and max_val <= 1E-12:
        return ('p', 1E-12)
    
    if max_val > 1E-12 and max_val <= 1E-7:
        return ('n', 1E-9)
    
    if max_val > 1E-7 and max_val <= 1E-4:
        return ('\u03BC', 1E-6)
    
    if max_val > 1E-4 and max_val <= 1E-3:
        return ('m', 1E-3)
    
    if max_val > 1E-3 and max_val <= 1000:
        return ('', 1)
    
    if max_val > 1e3 and max_val <= 1e6:
        return('k', 1e3)
    
    if max_val > 1e6:
        return('M', 1e6)

def plot_frequencies(freqs_fil, ft_V_fil, colors):
    fig, ax1 = plt.subplots()
    ax1.plot(freqs_fil, abs(ft_V_fil), 'o', color=colors[0])
    ax1.set_xscale('log')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')

def plot_Nyquist_ind(r_Z, i_Z, colors, units):
    fig, ax2 = plt.subplots()
    Cy_num = 0 #Zero is first cycle
    
    ax2.plot(r_Z[Cy_num], i_Z[Cy_num], color=colors[Cy_num],
             marker = 'o', markersize=8,
             label = f'Cycle {Cy_num}')
    plt.xlabel(f"Z ' ({units[0]}\u03A9)")
    plt.ylabel(f"- Z '' ({units[0]}\u03A9)")
    ax2.legend(fontsize='medium',
               labelcolor= colors[Cy_num])
    # plt.xlim(-2000,2000)
    # plt.ylim(-2000,2000)
    
def plot_Nyquist():
    r_Z = []
    i_Z = []
    count = 0
    
    ##Make color gradient with a start, stop, and number of plots
    cm_subsection = np.linspace(0, 1, NUM_SWEEPS)
    colors = [ cm.viridis(x) for x in cm_subsection ]
    
    fig, ax = plt.subplots()
    
    while count < NUM_SWEEPS:
        ##Automatically find the max V point at the highest frequency or manual
        AUTO = True
        if AUTO == True:
            num_of_pts = 20
            ys_near_highest_freq = ft_V[count][np.where(freqs[count] == highest_freq_from_gen)
                                       [0][0]-num_of_pts:
                                       np.where(freqs[count] == highest_freq_from_gen)
                                       [0][0]+num_of_pts]
            max_y_at_max_freq = max(abs(ys_near_highest_freq))
        else:
            max_y_at_max_freq = 10
        # print(max_y_at_max_freq)
        
        ##Removing the extra data points/frequencies!
        ft_I_fil  = ft_I[count][abs(ft_V[count]) >= max_y_at_max_freq]
        freqs_fil = freqs[count][abs(ft_V[count]) >= max_y_at_max_freq]
        ft_V_fil  = ft_V[count][abs(ft_V[count]) >= max_y_at_max_freq]
        
        ##Calculate impedence
        Z = ft_V_fil/ft_I_fil
        real_Z = np.real(Z)
        imag_Z = -np.imag(Z)
        
        ##Scale impedence based on units
        units = get_units(real_Z)
        r_Z.append(real_Z/units[1])
        i_Z.append(imag_Z/units[1])
        
        ##Option to plot whole Nyquist plot
        ax.plot(real_Z/units[1], imag_Z/units[1],
                color=colors[count], marker = 'o', markersize=8,
                label =  'One Cycle')
        plt.xlabel(f"Z ' ({units[0]}\u03A9)")
        plt.ylabel(f"- Z '' ({units[0]}\u03A9)")
        # plt.xlim(-2000,2000)
        # plt.ylim(-2000,2000)
        
        ##Option to plot each individual Nyquist plot
        # fig, ax2 = plt.subplots()
        # ax2.plot(real_Z/units[1], imag_Z/units[1],
        #         color=colors[count], marker = 'o', markersize=8,
        #         label = f'Cycle {count}')
        # plt.xlabel(f"Z ' ({units[0]}\u03A9)")
        # plt.ylabel(f"- Z '' ({units[0]}\u03A9)")
        # ax2.legend(fontsize='medium',
        #            labelcolor= colors[count])

        count +=1
    
    if NUM_SWEEPS == 1:
        ax.legend(fontsize='medium',
                  labelcolor= colors[0])
    if NUM_SWEEPS > 1:
        cbar = fig.colorbar(mappable=None, ax = ax, label='Cycles')
        cbar.ax.set_yticklabels(np.around(np.linspace(0, NUM_SWEEPS, 6), decimals=1))
    
    ##Option to plot Amplitude vs. Frequencies
    # plot_frequencies(freqs_fil, ft_V_fil, colors)
    
    ##Option to plot individual Nyquist plots based on cycle number
    # try:
    #     plot_Nyquist_ind(r_Z, i_Z, colors, units)
    # except:
    #     print('Cycle number may be out of bounds!')

def plot_CA():
    Is = []
    count = 0
    
    ##Make color gradient with a start, stop, and number of plots
    cm_subsection = np.linspace(0, 1, NUM_SWEEPS)
    colors = [ cm.viridis(x) for x in cm_subsection ]
    
    fig, ax = plt.subplots()
    
    while count < NUM_SWEEPS:
        ##Removing the extra data points/frequencies!
        t  = T[count]
        t1  = t[t>=0.5]
        i  = I[count][t>=0.5]
        
        ##Scale current based on units
        units = get_units(i)
        Is.append(i/units[1])
        
        ##Option to plot whole CA plot
        ax.plot(t1, i/units[1],
                color=colors[count],
                label =  'One Cycle',
                # rasterized=True,
                )
        plt.xlabel("Time (s)")
        plt.ylabel(f"Current ({units[0]}A)")
        count +=1
        
    if NUM_SWEEPS == 1:
        ax.legend(fontsize='medium',
                  labelcolor= colors[0])
    if NUM_SWEEPS > 1:
        cbar = fig.colorbar(mappable=None, ax = ax, label='Cycles')
        cbar.ax.set_yticklabels(np.around(np.linspace(0, NUM_SWEEPS, 6), decimals=1))

def plot_CV():
    Is = []
    count = 0
    
    ##Make color gradient with a start, stop, and number of plots
    cm_subsection = np.linspace(0, 1, NUM_SWEEPS)
    colors = [ cm.viridis(x) for x in cm_subsection ]
    
    fig, ax = plt.subplots()
    
    while count < NUM_SWEEPS:
        ##Removing the extra data points/frequencies!
        t  = T[count]
        v  = V[count][t>=0.01]
        i  = I[count][t>=0.01]
        
        ##Scale current based on units
        units = get_units(i)
        Is.append(i/units[1])
        
        ##Option to plot whole CV plot
        ax.plot(v, i/units[1],
                color=colors[count],
                label =  'One Cycle',
                linewidth=0.2)
        plt.xlabel("E vs. SCE (V)")
        plt.ylabel(f"Current ({units[0]}A)")
        count +=1
        
    if NUM_SWEEPS == 1:
        ax.legend(fontsize='medium',
                  labelcolor= colors[0])
    if NUM_SWEEPS > 1:
        cbar = fig.colorbar(mappable=None, ax = ax, label='Cycles')
        cbar.ax.set_yticklabels(np.around(np.linspace(0, NUM_SWEEPS, 6), decimals=1))
                                                  
                                                  
Ts, Vs, Is, sweeps = read_heka_data(file)
NUM_SWEEPS = sweeps[-1]
print('Number of cycles: ',NUM_SWEEPS)

##Split file by number of sweeps
T, V, I = (np.array_split(Ts, NUM_SWEEPS),
           np.array_split(Vs, NUM_SWEEPS),
           np.array_split(Is, NUM_SWEEPS))

ft_V  = []
ft_I  = []
freqs = []
count = 0
while count < NUM_SWEEPS:
    ft_V.append(np.fft.rfft(V[count])[1:])
    ft_I.append(np.fft.rfft(I[count])[1:])
    freqs.append(SAMPLE_FREQUENCY*np.fft.rfftfreq(len(V[count]))[1:])
    count +=1

# plot_Nyquist()
plot_CA()
plot_CV()

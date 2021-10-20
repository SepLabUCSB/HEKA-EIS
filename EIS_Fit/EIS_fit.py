import numpy as np
import ga
import circuits
import LEVM
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize, basinhopping, least_squares
import os
import time
plt.style.use('Z:/Projects/Brian/scientific.mplstyle')
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

'''
Based on ChemElectroChem 2021, 8, 2956–2967

doi.org/10.1002/celc.202100778
'''


path = r'C:\Users\BRoehrich\Desktop\EIS fit folder'

circuit = 'Randles_uelec'
bounds = {
    'R1': [1e-1, 1e9],
    'R2': [0.1, 1e9],
    'R3': [0.1, 1e9],
    'Q1': [1e-15, 1],
    'n1': [1,1],
    'Q2': [1e-15, 1],
    'n2': [0,1]
    }



'''
User inputs:
    circuit string
    bounds
    tolerence for fit

    folder containing all files to fit


Read data from file: freqs, re, im

Do genetic algorithm: fitted parameters

Do least squares fitting: refined parameters

Check if least squares fitting satisfies fit tolerence

No:
    Repeat genetic algorithm


Go to next file in batch, take refined parameters as initial values
for least squares fit


End: export csv of frequency, param 1, param 2, ...
            file 1
            file 2
            file 3
            ...

'''



class DataFile:
    
    def __init__(self, file, circuit, bounds, ax=None):
        
        df = pd.read_csv(file, skiprows=1, names=
                           ('freqs', 're', 'im'), sep='\t')
        
        self.file = file
        self.circuit = circuit
        self.bounds = bounds
        
        self.freqs = df['freqs'].to_numpy()
        self.re = df['re'].to_numpy()
        self.im = df['im'].to_numpy()
        self.Z = self.re + 1j*self.im
        
        self.params = dict()
        self.score = 1e9
        
        self.ax = ax
            
    
        
    def ga_fit(self, ax=None, starting_guess=None, **kwargs):
        if ax is not None:
            ax.plot(self.re/1e6, -self.im/1e6, 'o')
            
        self.params, self.score = ga.genetic_algorithm(
            self.freqs, self.Z, self.bounds, self.circuit, ax=ax,
            starting_guess = starting_guess, **kwargs)
        

        
        
    def LEVM_fit(self, **kwargs):
        try:
            self.params = LEVM.LEVM_fit(self.freqs, self.Z, 
                                        self.params, self.circuit)
        
        except:
            print('LEVM fit timed out, performing GA fit. File: ', 
                  self.file)
            self.ga_fit(starting_guess=self.params, n_iter = 50)
        
        # Fix handling of CPE phase!!
        self.params['n1'] = 1.0
        
        self.score = circuits.leastsq_errorfunc(self.freqs, self.Z,
                                                self.params, self.circuit)
        


def fit_all_runs(path):
    
    starting_time = time.time()
    
    for folder in os.listdir(path):
        
        folder_path = os.path.join(path, folder)
        
        df = {}
        i = 1
        for f in os.listdir(folder_path):
            
            # Iterate through all files in folder
            if f.endswith('s.txt'):
                
                file = os.path.join(folder_path, f)
                            
                df[i] = DataFile(file, circuit, bounds)
                
                if i == 1:
                    # Start new fit routine with genetic algorithm
                    fig, ax = plt.subplots()
                    while df[i].score > 100000:
                        df[i].ga_fit(n_iter=200)
                    
                    df[i].LEVM_fit()
                    
                    print('File 1 fit complete in ', 
                          time.time() - starting_time, 's.')
                
                else:
                    # Copy initial parameters from previous fit
                    df[i].params = df[i-1].params  
                    
                    df[i].LEVM_fit()

                        
                    if i%50 == 0:
                        print('File %s completed.' %i)
    
                
                i += 1
    print('Run complete. Total time: ', 
          time.time() - starting_time, 's.')
    
    return df







if __name__ == '__main__':
    
    df = fit_all_runs(path)
    
#%%    
    param_list = [key for key, item in df[1].params.items()]
    
    for param in param_list:
        l = []
        fig, ax = plt.subplots()
        for i in df:
            l.append(df[i].params[param])
        ax.plot(np.arange(0,45,0.1), l, '.')
        ax.set_xlabel('Time/ s')
        ax.set_ylabel(param)
        ax.set_title(param)
    
    
    scores = []
    for i in df:
        scores.append(df[i].score)
    fig, ax = plt.subplots()
    ax.plot(range(len(df)), scores)
    ax.set_ylabel('Score')




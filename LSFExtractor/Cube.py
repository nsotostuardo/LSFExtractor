import scipy
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from .Spectrum import Spectrum
from astropy.io import fits
from astropy.table import QTable


class Cube:
    def __init__(self, path, extension = 0, used_channels = 8) -> None:
        self.hdul = fits.open(path)
        self.imagen = self.hdul[extension]
        self.used_channels = used_channels
        self.x0 = [i for i in range(used_channels)]
        self.cube_kernel = []
        self.LSF = [0,0,0]

    def get_LSF(self):
        '''Executes the LSF estimation'''
        self.cube_corr_kernel()
        self.LSF_calc()
        return(self.LSF)
    
    def array_check(self, array):
        if len(array) > 1:
            return(array)
        else:
            return(self.array_check(array[0]))

    def cube_corr_kernel(self):
        '''Calculates the Kernel for the LSF aproximation'''
        correlation_values = []
        (y, x) = self.imagen.shape[-2:]
        for y0 in tqdm(range(0,y)):
            for x0 in range(0,x):
                slicer = self.cube_slicer(y0, x0)
                spectrum = self.imagen.data[slicer]
                spectrum = self.array_check(spectrum)
                correlation_values.append(self.cube_correlation(spectrum, self.used_channels))

        corr_values = np.transpose(correlation_values)
        y_up, y_mean, y_down = [], [], []
        for c_val in corr_values:
            c_val = c_val[~np.isnan(c_val)]
            d, mean, up = np.percentile(c_val, [16,50,84])
            y_up.append(up)
            y_down.append(d)
            y_mean.append(mean)

        self.cube_kernel = [y_down, y_mean, y_up]
        pass
        
    def LSF_calc(self):
        '''Estimates the LSF using the Kernel and the k factor'''
        for idx, y0 in enumerate(self.cube_kernel):
            kernel_correlation = self.kernel_correlation(y0)

            interpol_kernel = self.interpolate(self.x0, kernel_correlation)
            interpol_correlation = self.interpolate(self.x0, y0)
            self.k_factor = interpol_correlation/interpol_kernel

            y_shifted = np.interp(self.x0, np.array(self.x0) * self.k_factor, y0)
            y_shifted = list(y_shifted)

            if idx == 0 or idx == 2:
                y_shifted[0] = 0
            self.LSF[idx] = y_shifted[::-1] + y_shifted[1:]
            
        self.LSF[0], self.LSF[1] = self.LSF[1], self.LSF[0]

    def cube_slicer(self, y0, x0):
        '''Makes any dim slice '''
        dim = len(self.imagen.shape)
        slices = (slice(None),) * (dim - 2) + (y0, x0)
        return(slices)
        
    def cube_correlation(self, spectrum, channels):
        ''' Return Pearson product-moment correlation with a width of "channels" for any cube's spectrum'''
        spectrum = np.nan_to_num(spectrum)
        correlation = [1 if i == 0 
                else np.corrcoef(spectrum[:-1*i], spectrum[i:])[0][1] 
                for i in range(0, channels)
                ]
        return (correlation)
    
    def kernel_correlation(self, kernel, spect_channels = 27_583):
        ''' Return Pearson product-moment correlation between the LSF's kernel and a simulated spectrum'''
        spectrum = Spectrum(total_channels = spect_channels)
        kernel_spectr_corr = spectrum.get_correlation( np.array(kernel[::-1] + kernel[1:]), self.used_channels)
        return (kernel_spectr_corr)

    def plot_kernel(self):
        '''Plots estimated Kernel  '''
        (y_d, y0, y_u) = self.cube_kernel
        plt.plot(self.x0, y0, c = 'crimson')
        plt.fill_between(self.x0, np.array(y_d), np.array(y_u) ,
                        alpha = .5, color = 'lightcoral' )
        plt.errorbar(self.x0, y0, 
                    yerr = ( np.array(y0 - y_d), np.array(y0 - y_u) ), 
                            marker='o', markersize=8, capsize=7,
                            linestyle='none', c='crimson',
                            alpha = 1
                            )
        plt.xlabel('Channels')
        plt.ylabel('Correlation')
        plt.title('Cube Correlation Kernel')

    def plot_corr_LSF(self):
        plt.plot( self.x0, self.cube_kernel[1],  label = f'kernel')
        plt.plot( np.array(self.x0)*self.k_factor,
                self.cube_kernel[1],  label = f'kernel * k ')

        y_shifted = np.interp(self.x0,np.array(self.x0)*self.k_factor, self.cube_kernel[1])

        plt.scatter(self.x0, y_shifted, label = 'LSF')
        plt.legend()
        pass

    def interpolate(self, x, y, y_interpol = 0.5):
        '''Interpolates x values at y=0.5 using scipy'''
        x_interp = scipy.interpolate.interp1d(y, x)
        return(x_interp(y_interpol))

    def save_LSF(self, path_destino, format = '.3f', write = True):
        '''Saves LSF values into a _LSF.dat file'''
        try:
            assert self.LSF != [0,0,0], "LSF must be calculated fist with get_LSF method"
            t = QTable( [np.arange(-self.used_channels + 1, self.used_channels, 1), self.LSF[0], self.LSF[1], self.LSF[2]],
                    names=('Channels', 'LSF_50', 'LSF_16', 'LSF_84') 
                    )
            t['LSF_16'].info.format = format
            t['LSF_50'].info.format = format
            t['LSF_84'].info.format = format
            path_destino += "_LSF.dat"
            if write:
                t.write(path_destino, format='ascii.commented_header', overwrite=True)
            print('saved successfully')
            return(t)

        except AssertionError as msg:
            print(msg)
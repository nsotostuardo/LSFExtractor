import numpy as np

class Spectrum():

    def __init__(self, total_channels:int) -> None:
        self.channels : int = total_channels
        self.offset : np.ndarray = np.linspace(-1*total_channels/2, total_channels/2, total_channels)
        self.flux : np.ndarray = self.create_flux()
        self.correlations : dict = {}
        pass

    def create_flux(self, mu = 0, sigma = 1) -> np.ndarray:
        ''' Makes pseudo Flux with normal distribution'''
        dist = np.random.normal(loc=mu, scale=sigma, size=self.channels) 
        return(dist)
    
    def convolve(self, model) -> np.ndarray:
        ''' Convolves Spectrum with used Model'''
        return(np.convolve( self.flux, model(self.offset), 'same'))
    
    def get_correlation(self, kernel, n_channels:int):
        ''' Return Pearson product-moment correlation coefficients for n_channels width'''
        valor = np.convolve(self.flux, kernel,'same')
        corr = [1 if i ==0 else np.corrcoef(valor[:-1*i], valor[i:])[0][1] for i in range(0,n_channels)]
        return(corr)
    
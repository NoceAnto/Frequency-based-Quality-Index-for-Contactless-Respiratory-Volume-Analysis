import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt,periodogram
def butter_highpass(lowcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    b, a = butter(order, low, btype='high')
    return b, a
def butter_highpass_filter(data, lowcut, fs, order=5):
    b, a = butter_highpass(lowcut, fs, order=order)
    y = filtfilt(b, a, data)
    return y

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    """
    Apply a Butterworth bandpass filter to the input data.

    Parameters:
    - data: array-like, the input signal
    - lowcut: float, the lower frequency bound of the bandpass filter (Hz)
    - highcut: float, the upper frequency bound of the bandpass filter (Hz)
    - fs: float, the sampling frequency of the data (Hz)
    - order: int, the order of the filter (default is 5)

    Returns:
    - filtered_data: array-like, the filtered signal
    """
    nyq = 0.5 * fs  # Nyquist Frequency
    low = lowcut / nyq
    high = highcut / nyq

    b, a = butter(order, [low, high], btype='band')
    filtered_data = filtfilt(b, a, data)
    return filtered_data

def signal_power(sig):
    '''

    :param sig: signal amplitude in the time domain
    :return: signal power
    '''
    signal_length = np.size(sig)

    return np.sum(np.power(sig,2))/signal_length
def bandpower(Sxx,f, fth = [],f_mask=[],integration=True,mean=False):
    '''

    :param Sxx: Power Density periodogram, single side
    :param f:  frequency axis
    :param fth: [f_lower f_higher] --> lower and upper bound delimitating the frequency bands
    :param f_mask: True-False vector indicating the mask to consider
    :param integration: Boolean - if true, a simple rectangle base integration is used
    :param mean: Boolean - if true, a simple mean of Power Density
    :return:
    '''
    if len(fth)!=0:
        f_lower_th = fth[0]
        f_upper_th = fth[1]
        f_mask = (f>f_lower_th) & (f<f_upper_th)

    if integration:
        wantedPSD = Sxx[f_mask]
        P = sum(wantedPSD)*(f[1]-f[0]) #, f[ind_min: ind_max])
    if mean:
        P = np.mean(Sxx[f_mask])

    return P

def find_onset_offset(signal):
    """
    Finds the onset and offset of a 1-0 signal corresponding to the start and end of a 1 constant signal.

    Args:
        signal (list[int]): A list of 1s and 0s representing the signal.

    Returns:
        list[tuple[int, int]]: A list of tuples representing the onset and offset.
        Each tuple contains the start index and end index of a 1 constant signal.
    """
    onset_offset = []
    in_constant_signal = False
    start_index = None

    for i, value in enumerate(signal):
        if value == 1:
            if not in_constant_signal:
                # Start of 1 constant signal
                in_constant_signal = True
                start_index = i
        elif value == 0:
            if in_constant_signal:
                # End of 1 constant signal
                in_constant_signal = False
                onset_offset.append((start_index, i))

    # If the signal ends with a 1 constant signal
    if in_constant_signal:
        onset_offset.append((start_index, len(signal)-1))

    return onset_offset

def RNRfixed_window(f,Sxx,f1,f2):
    '''

    :param f: frequency axis
    :param Sxx: Power Density Spectrogram
    :param f1: lower frequency limit
    :param f2: upper frequency limit
    :return: RNR -> approximation of SNR,
            SigPowerEstimate -> approximation of signal power
            NoisePowerEstimate -> approximation of noise power
            dim_mask -> frequency mask dimension
    '''
    SigPowerEstimate = bandpower(Sxx, f, fth=[f1, f2], integration=True, mean=False)
    NoisePowerEstimate = bandpower(Sxx, f, fth=[0, f1], integration=True, mean=False) + bandpower(Sxx, f, fth=[f2, f[-1]], integration=True, mean=False)
    RNR = 10*np.log10(SigPowerEstimate/NoisePowerEstimate)
    dim_mask = f2-f1

    return RNR, SigPowerEstimate, NoisePowerEstimate,dim_mask

def RNRh(f,Sxx,df,n_harmonics=1,integration=True,peak_mean = False,peak_sum=False,show=False,path_where_to_save = []):
    '''

    :param f: frequency axis
    :param Sxx: Power Density spectrogram, single side
    :param df: 1/2 frequency interval around the considered harmonics
    :param n_harmonics: number of harmonics
    :param integration: if True, compute the normal RNRh with a rectangular approximation of the integral
    :param peak_mean: if True, compute the RNRp'; the signal power estimate is equal to the peak power
    in the respiratory interval 0.1 - 0.7 Hz and the noise power estimate is the mean power spectral density elsewhere
    :param peak_sum:if True, compute the RNRp'; the signal power estimate is equal to the peak power
    in the respiratory interval 0.1 - 0.7 Hz and the noise power estimate is the integral power spectral density elsewhere
    :param show: True/False to save an image of the frequency mask of the function
    :param path_where_to_save: path where to save the image
    :return:RNR -> approximation of SNR,
            SigPowerEstimate -> approximation of signal power
            NoisePowerEstimate -> approximation of noise power
            dim_mask -> frequency mask dimension
    '''

    # find the respiratory frequency as the max frequency in the interval
    S_respiratory_interv = Sxx[(f > 0.1) & (f < 1)]
    MaxPower_index= np.argmax(S_respiratory_interv)
    respiratory_interval = f[(f>0.1) & (f<1)]
    RespFreq = respiratory_interval[MaxPower_index]

    #find the n harmonics
    harmonics_vec = np.zeros(n_harmonics)
    mask = np.zeros(len(f),dtype=int)
    SigPowerEstimate = 0
    NoisePowerEstimate = 0

    harmonics_vec[0] = RespFreq

    if integration:
        indices = (f > max(harmonics_vec[0] - df, 0)) & (f < harmonics_vec[0] + df)

        for i in range(1,n_harmonics):
            harmonics_vec[i] = RespFreq * (i+1)

            indices_new = (f > max(harmonics_vec[i] - df,  0)) & (f < harmonics_vec[i] + df)
            indices = indices | indices_new

        mask[indices] = 1

        dimension_mask = sum(mask) * (f[1]-f[0])

        SigPowerEstimate = bandpower(Sxx,f,f_mask=indices)

        noise_indices = ~indices
        NoisePowerEstimate = bandpower(Sxx,f,f_mask=noise_indices)
        if show:
            plt.plot(f, mask*np.max(Sxx),label='mask')
            plt.plot(f,Sxx,label='power')
            plt.xlabel("Frequency (Hz)")
            plt.legend()
            plt.grid(True)
            #plt.show()
            plt.savefig(path_where_to_save)
            plt.close()
    if peak_mean:
        SigPowerEstimate = S_respiratory_interv[MaxPower_index]
        all_indices = np.arange(0,len(f))
        all_indices_beside_peak= all_indices!=MaxPower_index
        NoisePowerEstimate = np.mean(Sxx[all_indices_beside_peak])
        dimension_mask = f[1]-f[0]

    if peak_sum:
        SigPowerEstimate = S_respiratory_interv[MaxPower_index]
        all_indices = np.arange(0,len(f))
        all_indices_beside_peak= all_indices!=MaxPower_index
        NoisePowerEstimate = np.sum(Sxx[all_indices_beside_peak])
        dimension_mask = f[1]-f[0]

    RNR = 10*np.log10(SigPowerEstimate/NoisePowerEstimate)

    return RNR, SigPowerEstimate, NoisePowerEstimate,RespFreq,mask,dimension_mask


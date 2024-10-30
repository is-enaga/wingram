import numpy as np
from scipy.signal import butter, filtfilt, hilbert, decimate, detrend, correlate

from ..log import logger


def bandpass(
    data: np.ndarray,
    fs: float,
    fmin: float=None, 
    fmax: float=None,
    filt_order:int = 3,
    ):
    """
    チャンネルごとにバンドパスフィルターをかける．
    """
    if fmax is None and fmin is not None:
        b, a = butter(filt_order, fmin, btype='high', fs=fs)
    elif fmin is None and fmax is not None:
        if fmax > fs/2:
            fmax = fs / 2
            logger.warning(f"fmax is set to Nyquist frequency {fs/2} Hz (fs/2).")
        b, a = butter(filt_order, fmax, btype='low', fs=fs)
    else:
        if fmax > fs/2:
            fmax = fs / 2
            logger.warning(f"fmax is set to Nyquist frequency {fs/2} Hz (fs/2).")
        b, a = butter(filt_order, [fmin, fmax], btype='band', fs=fs)
    
    data = filtfilt(b,a,data,axis=0)
    
    return data

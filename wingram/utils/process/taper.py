import numpy as np


def taper(
    data: np.ndarray,
    taper_points: int,
):
    """
    Taper data.
    
    Parameters
    ----------
    data : np.ndarray
        Data to taper.
    taper_points : int
        Number of points to taper on both ends of the data.
        Length must be range of [0, len(data)//2].
    """
    taper = np.hanning(taper_points*2)
    data[:taper_points] *= taper[:taper_points]
    data[-taper_points:] *= taper[taper_points:]
    return data
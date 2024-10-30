import datetime
import numpy as np

def np2datetime(
    datetime64:np.datetime64,
):
    """
    Convert numpy datetime64 to datetime.datetime.
    """
    return datetime64.astype(datetime.datetime)

def np2timedelta(
    timedelta64:np.timedelta64,
):
    """
    Convert numpy timedelta64 to datetime.timedelta.
    """
    return timedelta64.item()
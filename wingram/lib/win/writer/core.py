import os
import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
import datetime
# from bitarray import bitarray
from ....utils.log import logger
from .helper import *

# ######################
# mk WIN FORMAT
# ######################
# ======================
# MAIN
# ======================
def __mkbin__(
    data: list[np.ndarray],
    fs:list[int],
    chnum:list[int] = None,
    starttime: datetime.datetime = None,
    yy:int = None,
    mm:int = None,
    dd:int = None,
    HH:int = None,
    MM:int = None,
    SS:int = None,
):
    """
    If both starttime and yy,mm,...,SS are given, starttime will be used.
    
    
    """
    # ######################
    # Check the input
    # ######################
    # =======================
    # data
    # =======================
    if isinstance(data, np.ndarray):
        if len(data.shape) == 1:
            data = [data]
    elif not isinstance(data, (list)):
        data = [data]
        
    # =======================
    # fs
    # =======================
    if isinstance(fs, (int,float)):
        fs = [fs]*len(data)
    else:
        if len(fs) != len(data):
            raise ValueError(f"The number of sampling frequency ({len(fs)}) and data ({len(data)}) should be same!")
    
    # =======================
    # chnum
    # =======================
    if chnum is None:
        chnum = list(range(len(data)))
    elif not isinstance(chnum, list):
        chnum = [chnum]
    if len(chnum) != len(data):
        raise ValueError(f"The number of channel ({len(chnum)}) and data ({len(data)})should be same!")
    
    # =======================
    # start time
    # =======================
    if starttime is None and (
        yy is None or mm is None or dd is None or 
        HH is None or MM is None or SS is None
    ):
        raise ValueError("Start time (starttime or yy,mm,...,SS) is required!")
    elif starttime is not None:
        yy = starttime.year % 100
        mm = starttime.month
        dd = starttime.day
        HH = starttime.hour
        MM = starttime.minute
        SS = starttime.second
    
    # ######################
    # PREPARE CHANNEL NUMBER
    # ######################
    if len(chnumber) is None:
        chnumber = list(range(len(data)))
    


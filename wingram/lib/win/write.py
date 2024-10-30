import os
import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
import datetime
# from bitarray import bitarray
from ...utils import *

# ######################
# mk WIN FORMAT
# ######################
# ======================
# MAIN
# ======================
def mkwin(
    data:np.array,
    sampling_freq:int,
    startdatetime: datetime.datetime = None,
    yy:int = None,
    mm:int = None,
    dd:int = None,
    HH:int = None,
    MM:int = None,
    SS:int = None,
    chnumber:list[int] = [],
    sample_size = 5,
    save = True,
    savedir = "./",
    savename = None,
    overwrite = False,
):
    """
    Generate winfile from 1D or 2D data array and its starttime and sampling frequency.
    Channel numbers and sample size can be given.
    
    Note
    ----------
    - Either of startdatetime or a set of yy,mm,dd,HH,MM,SS is neccesary. If both are given, startdatetime will be used.
    - Sampling frequency should be integer.
    
    Example
    ----------
    dat = (
        2**10 * np.cos(np.arange(0,550)*0.01*2*np.pi)
        ).astype(np.int32)
    start = datetime.datetime(1990,1,2,3,4,5,678900)
    mkwin(
        dat,
        start,
    )
    
    Parameters
    ----------
    data : np.array
        1D or 2D array. When a 2D array, axis 0 is channel axis and axis 1 is time axis.
    startdatetime : datetime.datetime, optional
        The starttime of data. 
        by default None
    yy : int, optional
    mm : int, optional
    dd : int, optional
    HH : int, optional
    MM : int, optional
    SS : int, optional
        Date and time of data, by default None.
    chnumber : list, optional
        A set of channel number in integer for output win data, by default [].
        In the output data, channel number will be written in a 4-digit hexadecimal.
    sample_size : int, optional
        Sample size mode, by default 5
        0: 0.5 byte is used to write each differential of amplitude. Not supoprted.
        1: 1 byte. Not supported.
        2: 2 byte
        3: 3 byte
        4: 4 byte
        5: 4 byte [Recommended] Values of data is interpreted as amplitude, not as differential of amplitude from a previous step. [Supported by WIN version >= 3]
    sampling_freq : int, optional
        Sampling frequency of the data, by default None
    save : bool, optional
        If true save WIN file, by default True
    savedir : str, optional
        A directory to save output WIN file, by default "./"
    savename : str, optional
        A file name of output WIN file, by default "out.win"
    overwrite : bool, optional
        If true overwrite output WIN file when file has same name already exists, by default False

    Returns
    -------
    bytearray
        A bytearray of output win binary string.
    """
    
    # ######################
    # CHECK THE START TIME
    # ######################
    if startdatetime is None and (
        yy is None or mm is None or dd is None or 
        HH is None or MM is None or SS is None
    ):
        raise ValueError("Start time (startdatetime or yy,mm,...,SS) is required!")
    
    # ######################
    # PREPARE CHANNEL NUMBER
    # ######################
    if len(chnumber)==0:
        chnumber = list(range(data.shape[-1]))
    
    # ######################
    # WAVE
    # ######################
    win = bytearray()
    
    if startdatetime != None:
        # ======================
        # PADDING
        # ======================
        # calc padding length for initial section.
        st = startdatetime
        winst = st - datetime.timedelta(microseconds=st.microsecond)
        logger.debug(f'st   : {st}')
        logger.debug(f'winst: {winst}')

        padst = int(datetime.timedelta(microseconds=st.microsecond).microseconds / 10**6 * sampling_freq)
        logger.debug(f'Initial padding points: {padst}')
        
        # Pad Initial Part ===================
        if padst > 0: 
            # generate padding shape
            if len(data.shape) == 1:
                padst_shape = (padst)
                # padding
                data = np.hstack([np.ones(padst_shape)*data[0], data])
                
            elif len(data.shape) == 2:
                padst_shape = (data.shape[0], padst)
                logger.debug(f'padst shape: {padst_shape}')
                # padding
                data = np.hstack([np.ones(padst_shape)*data[:,0].reshape(-1, 1), data])
                
            else:
                raise ValueError(f"Unexpected dimension of data! {len(data.shape)}")
            
        # calc padding length for last section: sampling f = number of 1sec. sample points
        padet = int(sampling_freq - (data.shape[-1] % sampling_freq))
        logger.debug(f'Ending padding points: {padet}')
        
        # Pad The Last Part ===================
        if 0 < padet < sampling_freq:
            if len(data.shape) == 1:
                padet_shape = (padet)
                # padding
                data = np.hstack([data, np.ones(padet_shape)*data[-1]])
                
            elif len(data.shape) == 2:
                padet_shape = (data.shape[0], padet)
                logger.debug(f"padet shape: {padet_shape}")
                # padding
                data = np.hstack([data, np.ones(padet_shape)*data[:,-1].reshape(-1, 1)])
                
            else:
                raise ValueError(f"Unexpected dimension of data! {len(data.shape)}")
        
        
        logger.debug(f"Total sample points: {data.shape[-1]}")
        # ======================
        # prepare start time
        # ======================
        yy = int(winst.strftime("%y"))
        mm = winst.month
        dd = winst.day
        HH = winst.hour
        MM = winst.minute
        SS = winst.second
        logger.debug(f"start: {yy}/{mm}/{dd}-{HH}:{MM}:{SS}")
        
    # ######################
    # split into 1sec. sections
    # ######################
    if len(data.shape) == 1:
        itrs = int(np.ceil(data.shape[-1] / sampling_freq))
        
        # process for each seconds  ===================
        for i in range(itrs): # number of samples
            win1s = bytearray()
            data1s = data[i*sampling_freq:(i+1)*sampling_freq]
            logger.debug(f"data1s: {i}: {len(data1s)}")
            win1s.extend(__mkwin1chblock__(data1s,chnumber[0],sample_size,sampling_freq))
            
            # header ================
            win1s[0:0] = __mkwinheader_st__(yy,mm,dd,HH,MM,SS)
            win1s[0:0] = __mkwinheader_size__(win1s)
            win.extend(win1s)
            
            # win[0:0] = __mkwinheader_size__(win)
        
    elif len(data.shape) == 2:
        itrs = int(np.ceil(data.shape[-1] / sampling_freq))
        
        # process for each seconds  ===================
        logger.debug(f"data shape: {data.shape}")
        logger.debug(f"itrs: {itrs}")
        # ax.plot(data[0])
        for i in range(itrs): # number of samples
            logger.debug(f"Processing: {i*sampling_freq} - {(i+1)*sampling_freq}")
            win1s = bytearray()
            data1s = data[:, i*sampling_freq:(i+1)*sampling_freq]
            logger.debug(f"data1s: {i}: {data1s.shape}")

            # process for each channel  ===================
            for ch in range(data.shape[0]):
                win1s.extend(__mkwin1chblock__(data1s[ch],chnumber[ch],sample_size,sampling_freq))
                
            # header ================
            win1s[0:0] = __mkwinheader_st__(yy,mm,dd,HH,MM,SS)
            win1s[0:0] = __mkwinheader_size__(win1s)
            win.extend(win1s)
            
            # Next time ==============
            if 70 < yy <= 99:
                year = yy + 1000
            elif 0 <= yy < 69:
                year = yy + 2000 
            itr_datetime = datetime.datetime(year,mm,dd,HH,MM,SS)
            itr_datetime = itr_datetime + datetime.timedelta(seconds=1)
            yy = int(itr_datetime.strftime("%y"))
            mm = itr_datetime.month
            dd = itr_datetime.day
            HH = itr_datetime.hour
            MM = itr_datetime.minute
            SS = itr_datetime.second
            
            logger.debug(f"Total: {len(win)} Byte")

    
    if save:
        # SAVE NAME ===================
        if savename is None:
            # savename = f'{yy:02.0f}{mm:02.0f}{dd:02.0f}.{HH:02.0f}{MM:02.0f}{SS:02.0f}_{min(chnumber)}-{max(chnumber)}-{len(chnumber)}ch.win'
            savename = f'{yy:02.0f}{mm:02.0f}{dd:02.0f}.{HH:02.0f}{MM:02.0f}{SS:02.0f}'
            
        # SAVE ===================
        savefp = os.path.join(savedir, savename)
        if not os.path.exists(savefp) or overwrite:
            with open(savefp, 'wb') as f:
                f.write(win)
            logger.info(f"SAVED: {savefp}")

        elif os.path.exists(savefp) and not overwrite:
            logger.error(f"File already exists! {savefp}")
        
    return win

# ======================
# HELPER
# ======================
def __mkwinheader_size__(
    win: bytearray
):
    """
    Generate the first part of win header based on a input win data which has all other required parts.
    Input win byte string should has all of:
    - Start time of the header
    - Channel header
    - Channel data
    """
    header = bytearray()
    # file size ==========
    wholebyte = 4 + (len(win)) # 4 is this header's size
    
    # Add a header =========== 
    header.extend(wholebyte.to_bytes(4,'big',signed=False))
    
    return header
    
def __mkwinheader_st__(
    yy: int = 90,
    mm:int = 1,
    dd:int = 1,
    HH:int = 0,
    MM:int = 0,
    SS:int = 0,
):
    """
    Return a binary array for a start time header of win format
    """
    def catnybble(
        n1,
        n2,
        ):
        nybble = 2**4
        return (n1 << 0x4 | n2).to_bytes(1,'big',signed=False)
    
    out = bytearray()
    
    out.extend(catnybble(yy//10,yy%10))
    out.extend(catnybble(mm//10,mm%10))
    out.extend(catnybble(dd//10,dd%10))
    out.extend(catnybble(HH//10,HH%10))
    out.extend(catnybble(MM//10,MM%10))
    out.extend(catnybble(SS//10,SS%10))
    return out

def __mkwin1chblock__(
    data,
    chnumber = 0x10,
    sample_size = 5,
    sampling_freq = 100,
    ):
    """
    Return a byte string converted from input data array.
    samplesize 5 is supported by only win version > 3.
    
    Args:
    ==
    sample_size: default is 5.
        Indicates size of each sample in byte and writing method of data.
        Takes value of 0,1,2,3,4,or5.
        0: 0.5 byte
        1-4: n byte
        5: 4 byte but data is intepreted as 
        
        The first sample is treated as 4 byte integer regardless to the sample size.
        Only samples after the 2nd sample is converted into the above size.
    """
    win = bytearray()
    
    # #####################
    # CHANNEL HEADER [4B]
    # #####################
    # ======================
    # ch number [2B]
    # ======================
    # write --------
    win.extend(
        int(chnumber).to_bytes(2,'big',signed=False)
    )
    # ======================
    # data size[0.5B], sampling_freq [1.5B]
    # ======================
    # write --------
    win.extend(
        (sample_size*16**3
         +sampling_freq).to_bytes(2,'big',signed=False)
        )
    
    # #######################
    # data [4B] 
    # ######################
    # ======================
    # Check
    # ======================
    # Chack data length ================
    if len(data) > sampling_freq:
        # data = data[:sampling_freq]
        raise ValueError(f"Data length {len(data)} is inconsistent to sampling frequency {sampling_freq}Hz.")
    
    # Check endian type ================
    # TODO 0, 1のときの型
    if sample_size == 0:
        raise ValueError(f"Sample size {sample_size} is not supported for now.")
    if sample_size == 1:
        dtype = None
        raise ValueError(f"Sample size {sample_size} is not supported for now.")
    elif sample_size == 2:
        dtype = np.int8
    elif sample_size == 3:
        dtype = np.int16
    elif sample_size == 4 or sample_size == 5:
        dtype = np.int32
    else:
        raise ValueError(f"Unexpected sample size!: {sample_size}")
    
    # ======================
    # Convert data into byte strings 
    # ======================
    if sample_size == 5:
        data = data.astype(dtype).byteswap().tobytes()
        # write --------
        win.extend(data)
    else:
        # sample_size = 0,1,2,3,4
        # First Sample -------------
        _data = data[0].astype(np.int32).byteswap().tobytes()
        win.extend(_data)
        # Rest Samples ------------
        _data = data[1:] - data[:-1]
        _data = _data.astype(dtype).byteswap().tobytes()
        # write --------
        win.extend(_data)
    
    return win

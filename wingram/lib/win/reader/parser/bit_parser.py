"""
Modules for parsing WIN data (2024/09/14).
"""
import numpy as np
# import xarray as xr
import datetime
import pandas as pd
from bitarray import bitarray

from .....utils.log import logger
from .....utils.timehandler import yy2yyyy
from .....utils.int_bit import bit2signint
def __get_starttime__(
    bitarray1s:bitarray,
):  
    bitloc = 0
    # start time 6B -----------
    yy = (
        int(bitarray1s[bitloc+3*8 : bitloc+3*8+4].to01(),2)*10
        +
        int(bitarray1s[bitloc+3*8+4 : bitloc+4*8].to01(),2)
    )
    mm = (
        int(bitarray1s[bitloc+4*8 : bitloc+4*8+4].to01(),2)*10
        +
        int(bitarray1s[bitloc+4*8+4 : bitloc+5*8].to01(),2)
    )
    dd = (
        int(bitarray1s[bitloc+5*8 : bitloc+5*8+4].to01(),2)*10
        +
        int(bitarray1s[bitloc+5*8+4 : bitloc+6*8].to01(),2)
    )
    HH = (
        int(bitarray1s[bitloc+6*8 : bitloc+6*8+4].to01(),2)*10
        +
        int(bitarray1s[bitloc+6*8+4 : bitloc+7*8].to01(),2)
    )
    MM = (
        int(bitarray1s[bitloc+7*8 : bitloc+7*8+4].to01(),2)*10
        +
        int(bitarray1s[bitloc+7*8+4 : bitloc+8*8].to01(),2)
    )
    SS = (
        int(bitarray1s[bitloc+8*8 : bitloc+8*8+4].to01(),2)*10
        +
        int(bitarray1s[bitloc+8*8+4 : bitloc+9*8].to01(),2)
    )
    
    # yy to yyyy ----------------------
    yyyy = yy2yyyy(yy)
        
    startdatetime = datetime.datetime(yyyy,mm,dd,HH,MM,SS)
    logger.debug(f"time {yy}/{mm}/{dd}-{HH}:{MM}:{SS}")
    return startdatetime

def __read_1s_header__(
    bit1s: bitarray,
):
    bitloc = 0
    # 1s data length [4B] -----------
    bytesize = int(bit1s[bitloc:bitloc+3*8].to01(),2)
        
    logger.debug(f"1s size {bytesize} B")
    
    # start time 6B -----------
    yy = (
        int(bit1s[bitloc+3*8 : bitloc+3*8+4].to01(),2)*10
        +
        int(bit1s[bitloc+3*8+4 : bitloc+4*8].to01(),2)
    )
    mm = (
        int(bit1s[bitloc+4*8 : bitloc+4*8+4].to01(),2)*10
        +
        int(bit1s[bitloc+4*8+4 : bitloc+5*8].to01(),2)
    )
    dd = (
        int(bit1s[bitloc+5*8 : bitloc+5*8+4].to01(),2)*10
        +
        int(bit1s[bitloc+5*8+4 : bitloc+6*8].to01(),2)
    )
    HH = (
        int(bit1s[bitloc+6*8 : bitloc+6*8+4].to01(),2)*10
        +
        int(bit1s[bitloc+6*8+4 : bitloc+7*8].to01(),2)
    )
    MM = (
        int(bit1s[bitloc+7*8 : bitloc+7*8+4].to01(),2)*10
        +
        int(bit1s[bitloc+7*8+4 : bitloc+8*8].to01(),2)
    )
    SS = (
        int(bit1s[bitloc+8*8 : bitloc+8*8+4].to01(),2)*10
        +
        int(bit1s[bitloc+8*8+4 : bitloc+9*8].to01(),2)
    )
    logger.debug(f"time {yy}/{mm}/{dd}-{HH}:{MM}:{SS}")
    # yy to yyyy ----------------------
    yyyy = yy2yyyy(yy)
        
    startdatetime = datetime.datetime(yyyy,mm,dd,HH,MM,SS)
    logger.debug(f"time {yy}/{mm}/{dd}-{HH}:{MM}:{SS}")
    return bytesize, startdatetime

def __split1s__(
    fp:str,
    return_starttime:bool = False,
):
    """
    Open WIN file and split into each 1s segment.
    """
    # =======================
    # read
    # =======================
    with open(fp, 'rb') as f:
        raw = f.read()
    bitdata = bitarray(
        raw,
        endian='big',
        )
    
    # =======================
    # split bitdata into each 1 sec segment
    # =======================
    bitloc = 0
    bit_segments = []
    starttimes = []
    while bitloc < len(bitdata):
        logger.debug(f"{bitloc}/{len(bitdata)}")
        # 1s data length [4B] [Actually 3B?]-----------
        bytesize = int(bitdata[bitloc:bitloc+3*8].to01(),2)
        
        segment = bitdata[bitloc:bitloc+bytesize*8]
        bit_segments.append(segment)
        
        # logger.debug(f"1s size {bytesize} B")
        
        if return_starttime:
            starttimes.append(__get_starttime__(segment))
        bitloc += bytesize*8
    
    logger.debug(f"{len(bit_segments)} s segments are found.")
    
    if return_starttime:
        return bit_segments, starttimes
    else:
        return bit_segments

def __read_1chbit__(
    bit1ch:bitarray,
    starttime:datetime.datetime = None,
):
    """
    Convert 1s 1 channel unit bit data to numpy array.
    
    Parameters
    ----------
    bit1ch: bitarray
        1s 1 channel unit bit data.
    """
    bitloc = 0
    # ----------------------
    # Header 4B
    # ----------------------
    # # channel number 2B -----------
    # chnum = int(bit1ch[bitloc : bitloc+2*8].to01(),2)
    # chnum = format(chnum,'04x')
    # logger.debug(f"chnum: {chnum}")

    # sample size [Byte] 0.5B -----------
    sample_size = int(bit1ch[bitloc+2*8 : bitloc+2*8+4].to01(),2)
    if sample_size == 0:
        bitstep = 4
    elif sample_size == 1 or sample_size == 2 or sample_size == 3 or sample_size == 4:
        bitstep = sample_size*8
    elif sample_size == 5:
        bitstep = 4*8
    else:
        raise ValueError(f"Unexpected sample size: {sample_size}.")
    logger.debug(f"sample_size: {sample_size}")
    logger.debug(f"bitstep: {bitstep}")
    # sampling rate 1.5B -----------
    fs =  int(bit1ch[bitloc+2*8+4 : bitloc+4*8].to01(),2)
    logger.debug(f"fs: {fs}Hz")
    
    # header 4B + data[0]4B + data[1:] ---------
    n_1ch = 4*8 + 4*8 + bitstep*(fs-1)
    
    # ----------------------
    # data
    # ----------------------
    bitloc += 4*8
    data = np.zeros((2,fs),dtype=object)*np.nan
    
    # first sample 4B -----------
    data[0,0] = bit2signint(bit1ch[bitloc:bitloc+4*8].to01())
    
    bitloc += 4*8
    # rest data -----------
    for i in range(1,fs):
        data[0,i] = bit2signint(bit1ch[bitloc:bitloc+bitstep].to01(),bitstep)
        bitloc += bitstep
    # difference to absolute -----------
    if sample_size != 5:
        data[0] = np.cumsum(data[0])
    
    # time axis -----------
    if starttime is not None:
        endtime = starttime + datetime.timedelta(seconds=1)
        dt = datetime.timedelta(seconds=1/fs)
        time = np.arange(
            starttime,
            endtime,
            dt,
        )
        data[1] = time
        # logger.info(f"time {time.shape}")
        # logger.info(f"data {data.shape}")
        # xrdata = xr.DataArray(
        #     data,
        #     coords = {
        #         'time':time,
        #         },
        #     dims = [
        #         'time',
        #         ],
        #     )
    return data

def __split_1s_to_1ch__(
    bit1s:bitarray,
    # chnumber:list[str] = None,
):
    """
    
    
    """
    # =======================
    # split 1s bitdata into each channels
    # =======================
    # =======================
    # starttime 6B
    # =======================
    starttime = __get_starttime__(bit1s)
    
    # =======================
    # Channel unit data
    # =======================
    # bit loc start after 1sec header
    bitloc = 9*8
    chs = [] # channel number
    bit1chs = [] # data of each channel
    chdatalist = [] 
    while bitloc < len(bit1s)-9*8:
        logger.debug(f"{bitloc}/{len(bit1s)-9*8}")
        
        # channel number 2B -----------
        chnum = int(bit1s[bitloc : bitloc+2*8].to01(),2)
        chnum = format(chnum,'04x')
        
        # convert chnum to UPPER CASE
        chnum = chnum.upper()
        
        chs.append(chnum)
        logger.debug(f"chnum: {chnum}")

        # sample size [Byte] 0.5B -----------
        sample_size = int(bit1s[bitloc+2*8 : bitloc+2*8+4].to01(),2)
        if sample_size == 0:
            bitstep = 4
        elif sample_size == 1 or sample_size == 2 or sample_size == 3 or sample_size == 4:
            bitstep = sample_size*8
        elif sample_size == 5:
            bitstep = 4*8
        else:
            raise ValueError(f"Unexpected sample size: {sample_size}.")
        logger.debug(f"sample_size: {sample_size}")
        logger.debug(f"bitstep: {bitstep}")
        # sampling rate 1.5B -----------
        fs =  int(bit1s[bitloc+2*8+4 : bitloc+4*8].to01(),2)
        logger.debug(f"fs: {fs}Hz")
        
        # header 4B + data[0]4B + data[1:] ---------
        n_1ch = 4*8 + 4*8 + bitstep*(fs-1)
        if bitstep*(fs-1)%8 != 0:
            n_1ch += 4
        logger.debug(f"n_1ch: {n_1ch/8} B; {n_1ch} bit")
        
        # =======================
        # data
        # =======================
        chdatalist.append(
            __read_1chbit__(
                bit1s[bitloc:bitloc+n_1ch],
                starttime = starttime,
                )
        )
        
        bit1chs.append(bit1s[bitloc:bitloc + n_1ch])
        bitloc += n_1ch
    logger.debug(f"{len(chs)} ch segments are found.")
    return chs, chdatalist
    
    
    # df = pd.Series(
    #     chdatalist,
    #     index = chs,
    #     )
    # if chnumber is not None:
    #     if not isinstance(chnumber, list):
    #         chnumber = [chnumber]
    #     df = df.loc[chnumber]
    # return df
    
def __1s_to_ch__(
    bit1s:bitarray,
    ) -> list[bitarray]:
    """
    For debugging.
    Split 1 sec data to channel data.
    Use after __split1s__.
    (created 2024/09/21)
    
    Parameters
    ----------
    bitarray: bitarray
        bitarray of 1 s WIN data.
    """
    # =======================
    # Channel unit data
    # =======================
    # bit loc start after 1sec header
    bitloc = 9*8
    
    out = []
    while bitloc < len(bit1s)-9*8:
        logger.debug(f"{bitloc}/{len(bit1s)-9*8}")

        # sample size [Byte] 0.5B -----------
        sample_size = int(bit1s[bitloc+2*8 : bitloc+2*8+4].to01(),2)
        if sample_size == 0:
            bitstep = 4
        elif sample_size == 1 or sample_size == 2 or sample_size == 3 or sample_size == 4:
            bitstep = sample_size*8
        elif sample_size == 5:
            bitstep = 4*8
        else:
            raise ValueError(f"Unexpected sample size: {sample_size}.")
        logger.debug(f"sample_size: {sample_size}")
        logger.debug(f"bitstep: {bitstep}")
        # sampling rate 1.5B -----------
        fs =  int(bit1s[bitloc+2*8+4 : bitloc+4*8].to01(),2)
        logger.debug(f"fs: {fs}Hz")
        
        # ch header 4B + data[0]4B + data[1:] ---------
        n_1ch = 4*8 + 4*8 + bitstep*(fs-1)
        if bitstep*(fs-1)%8 != 0:
            n_1ch += 4
        # logger.debug(f"n_1ch: {n_1ch/8} B; {n_1ch} bit")
        
        out.append(bit1s[bitloc:bitloc + n_1ch])
        bitloc += n_1ch
    # out.append(bit1s[bitloc:])
    return out

def __read_chheader__(
    bit1ch:bitarray,
    ):
    """
    Get channel header.
    (created 2024/09/21)
    """
    bitloc = 0
    # channel number 2B -----------
    chnum = int(bit1ch[bitloc : bitloc+2*8].to01(),2)
    chnum = format(chnum,'04x')
    logger.debug(f"chnum: {chnum}")

    # sample size [Byte] 0.5B -----------
    sample_size = int(bit1ch[bitloc+2*8 : bitloc+2*8+4].to01(),2)
    if sample_size == 0:
        bitstep = 4
    elif sample_size == 1 or sample_size == 2 or sample_size == 3 or sample_size == 4:
        bitstep = sample_size*8
    elif sample_size == 5:
        bitstep = 4*8
    else:
        raise ValueError(f"Unexpected sample size: {sample_size}.")
    logger.debug(f"sample_size: {sample_size}")
    logger.debug(f"bitstep: {bitstep}")
    # sampling rate 1.5B -----------
    fs =  int(bit1ch[bitloc+2*8+4 : bitloc+4*8].to01(),2)
    logger.debug(f"fs: {fs}Hz")
    
    # header 4B + data[0]4B + data[1:] ---------
    n_1ch = 4*8 + 4*8 + bitstep*(fs-1)
    
    # logger.info(
    #     f"\n{chnum:>4}|{sample_size:>1}|{fs:>3}\n"
    #     f"{bit1ch[bitloc:bitloc+8*2].tobytes().hex()}|{bit1ch[bitloc+8*2:bitloc+8*2+4].tobytes().hex()}|{bit1ch[bitloc+8*2+4:bitloc+8*4].tobytes().hex()}")
    
    return chnum, sample_size, fs, n_1ch
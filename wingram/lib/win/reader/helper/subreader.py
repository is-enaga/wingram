"""
Old version of WIN reader.
No longer used.(2024/09/14)
"""

import numpy as np
import datetime

from bitarray import bitarray

from .....utils.log import logger
from .....utils.timehandler import yy2yyyy


def getheaderlocs(bits:bitarray)->list[int]:
    """
    Get locations on bit array of each 1s sections.
    
    Parameters
    ----------
    bits: bitarray
        Bit array of WIN binary data.
    
    Returns
    -------
    table: np.array
        Table of each 1s sections.
        Each row contains [location in bit, size[B], start datetime].
    """
    bitlocs = []
    bitloc = 0
    bytesizes = []
    starttimes = []
    # ----------------------
    # header 10B
    # ----------------------
    while bitloc < len(bits):
        bitlocs.append(bitloc)
        # size in Byte 4B -----------
        bytesize = int(bits[bitloc:bitloc+3*8].to01(),2)
        bytesizes.append(bytesize)
        logger.debug(f"1s size {bytesize} B")
        
        # start time 6B -----------
        yy = (
            int(bits[bitloc+3*8 : bitloc+3*8+4].to01(),2)*10
            +
            int(bits[bitloc+3*8+4 : bitloc+4*8].to01(),2)
        )
        mm = (
            int(bits[bitloc+4*8 : bitloc+4*8+4].to01(),2)*10
            +
            int(bits[bitloc+4*8+4 : bitloc+5*8].to01(),2)
        )
        dd = (
            int(bits[bitloc+5*8 : bitloc+5*8+4].to01(),2)*10
            +
            int(bits[bitloc+5*8+4 : bitloc+6*8].to01(),2)
        )
        HH = (
            int(bits[bitloc+6*8 : bitloc+6*8+4].to01(),2)*10
            +
            int(bits[bitloc+6*8+4 : bitloc+7*8].to01(),2)
        )
        MM = (
            int(bits[bitloc+7*8 : bitloc+7*8+4].to01(),2)*10
            +
            int(bits[bitloc+7*8+4 : bitloc+8*8].to01(),2)
        )
        SS = (
            int(bits[bitloc+8*8 : bitloc+8*8+4].to01(),2)*10
            +
            int(bits[bitloc+8*8+4 : bitloc+9*8].to01(),2)
        )
        
        # yy to yyyy ----------------------
        yyyy = yy2yyyy(yy)
            
        startdatetime = datetime.datetime(yyyy,mm,dd,HH,MM,SS)
        logger.debug(f"time {yy}/{mm}/{dd}-{HH}:{MM}:{SS}")
        starttimes.append(startdatetime)
        
        bitloc += bytesize*8
        
    bitlocs = np.array(bitlocs)
    bytesizes = np.array(bytesizes)
    starttimes = np.array(starttimes)
    table = np.vstack([bitlocs,bytesizes,starttimes]).T
    return table

def bit2signint(bit:str, bitsize:int = None):
    """
    Convert bit string to signed integer.
    Used when read WIN data.
    Args
    ----
    bit: str
        bit string
    bitsize: int
        bit size for conversion to signed integer. 
    """
    if bitsize is None:
        bitsize = len(bit)
    out = int(bit,2)
    if out >= 2**(bitsize-1):
        out -= 2**bitsize
    return out

def read1sheader(fp,stbit=0):
    with open(fp, 'rb') as f:
        bi = f.read()
    bi = bitarray(
        bi,
        endian='big',
        )
    # ----------------------
    # header 10B
    # ----------------------
    # size in Byte 4B -----------
    size = int(bi[stbit:stbit+3*8].to01(),2)
    print("1s size", size)

    # start time 6B -----------
    yy = (
        int(bi[stbit+3*8 : stbit+3*8+4].to01(),2)*10
        +
        int(bi[stbit+3*8+4 : stbit+4*8].to01(),2)
    )
    mm = (
        int(bi[stbit+4*8 : stbit+4*8+4].to01(),2)*10
        +
        int(bi[stbit+4*8+4 : stbit+5*8].to01(),2)
    )
    dd = (
        int(bi[stbit+5*8 : stbit+5*8+4].to01(),2)*10
        +
        int(bi[stbit+5*8+4 : stbit+6*8].to01(),2)
    )
    HH = (
        int(bi[stbit+6*8 : stbit+6*8+4].to01(),2)*10
        +
        int(bi[stbit+6*8+4 : stbit+7*8].to01(),2)
    )
    MM = (
        int(bi[stbit+7*8 : stbit+7*8+4].to01(),2)*10
        +
        int(bi[stbit+7*8+4 : stbit+8*8].to01(),2)
    )
    SS = (
        int(bi[stbit+8*8 : stbit+8*8+4].to01(),2)*10
        +
        int(bi[stbit+8*8+4 : stbit+9*8].to01(),2)
    )
    
    # yy to yyyy ----------------------
    yyyy = yy2yyyy(yy)
        
    startdatetime = datetime.datetime(yyyy,mm,dd,HH,MM,SS)
    logger.debug(f"time {yy}/{mm}/{dd}-{HH}:{MM}:{SS}")
    return size, startdatetime

def read1chheader(fp,stchbit=9*8):
    with open(fp, 'rb') as f:
        bi = f.read()
    bi = bitarray(
        bi,
        endian='big',
        )    
    # ----------------------
    # channel header 4B
    # ----------------------
    # channel number 2B -----------
    chnum = int(bi[stchbit : stchbit+2*8].to01(),2)
    chnum = format(chnum,'04x')
    print("chnum",chnum)

    # sample size [Byte] 0.5B -----------
    sample_size = int(bi[stchbit+2*8 : stchbit+2*8+4].to01(),2)
    print("sample size",sample_size)
    if sample_size == 0:
        bitstep = 4
    elif sample_size == 5:
        bitstep = 4*8
    else:
        bitstep = sample_size*8
    print("data bit size",bitstep)

    # sampling rate 1.5B -----------
    fs =  int(bi[stchbit+2*8+4 : stchbit+4*8].to01(),2)
    print("sampling rate",fs)
    return chnum, bitstep, fs

def __read1ch__(fp, stchbit=9*8):
    with open(fp, 'rb') as f:
        bi = f.read()
    bi = bitarray(
        bi,
        endian='big',
        )
    # ----------------------
    # channel header 4B
    # ----------------------
    # channel number 2B -----------
    chnum = int(bi[stchbit : stchbit+2*8].to01(),2)
    chnum = format(chnum,'04x')
    logger.debug(f"ch number: {chnum}")
    
    # sample size [Byte] 0.5B -----------
    sample_size = int(bi[stchbit+2*8 : stchbit+2*8+4].to01(),2)
    logger.debug(f"sample_size: {sample_size}")
    if sample_size == 0:
        bitstep = 4
    elif sample_size == 5:
        bitstep = 4*8
    else:
        bitstep = sample_size*8
    logger.debug(f"bit step: {bitstep} step")
    # sampling rate 1.5B -----------
    fs =  int(bi[stchbit+2*8+4 : stchbit+4*8].to01(),2)
    logger.debug(f"fs: {fs}Hz")
    # ----------------------
    # data
    # ----------------------
    bit = stchbit + 4*8
    data = np.zeros(fs)*np.nan
    
    # first sample 4B -----------
    data[0] = bit2signint(bi[bit:bit+4*8].to01())
    
    bit += 4*8
    # rest data -----------
    for i in range(1,fs):
        data[i] = bit2signint(bi[bit:bit+bitstep].to01(),bitstep)
        bit += bitstep
        
    if sample_size == 0 and fs%2 == 0:
        bit += 4
    
    # difference to absolute -----------
    if sample_size != 5:
        data = np.cumsum(data)
    params = {
        "ch": chnum,
        # "sample_size": sample_size,
        "bit_size": bitstep,
        "fs": fs,
    }
    return params, data


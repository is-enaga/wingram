import numpy as np
import datetime
import bitarray
from ....utils.int_bit import int2bin, intarray2bin
from ....utils.log import logger

# ======================
# HELPER
# ======================
def __add_header__(
    badata: bitarray.bitarray,
    starttime: datetime.datetime = None,
    yy:int = None,
    mm:int = None,
    dd:int = None,
    HH:int = None,
    MM:int = None,
    SS:int = None,
) -> bitarray.bitarray:
    """
    Add header to data of channels.
    This function completes the 1s WIN format data
    from single or multiple channel data.

    starttime can be given in two ways.
    1. starttime: datetime.datetime
    2. yy,mm,dd,HH,MM,SS: int
    If both are given, starttime is used.
    
    Parameters
    ----------
    badata : bitarray.bitarray
        Binary data of 1 or more channels.
    starttime : datetime.datetime
        Start time of the data.
    yy : int
        Last 2 digits of year of start time.
    mm : int
        Month of start time.
    dd : int
        Day of start time.
    HH : int
        Hour of start time.
    MM : int
        Minute of start time.
    SS : int
        Second of start time.
        
    Returns
    -------
    out: bitarray.bitarray
        1s data with header in WIN format.
    """
    # ##########################
    # Check input
    # ##########################
    if starttime is None and (yy is None or mm is None or dd is None or HH is None or MM is None or SS is None):
        raise ValueError("starttime or yy,mm,dd,HH,MM,SS must be given.")
    if starttime is not None:
        yy = starttime.year % 100
        mm = starttime.month
        dd = starttime.day
        HH = starttime.hour
        MM = starttime.minute
        SS = starttime.second
    else:
        if yy is None or mm is None or dd is None or HH is None or MM is None or SS is None:
            raise ValueError("starttime or yy,mm,dd,HH,MM,SS must be given.")
        elif yy < 0 or yy > 99:
            raise ValueError(f"yy must be in [0,99]. Given {yy}.")
        elif mm < 1 or mm > 12:
            raise ValueError(f"mm must be in [1,12]. Given {mm}.")
        elif dd < 1 or dd > 31:
            raise ValueError(f"dd must be in [1,31]. Given {dd}.")
        elif HH < 0 or HH > 23:
            raise ValueError(f"HH must be in [0,23]. Given {HH}.")
        elif MM < 0 or MM > 59:
            raise ValueError(f"MM must be in [0,59]. Given {MM}.")
        elif SS < 0 or SS > 59:
            raise ValueError(f"SS must be in [0,59]. Given {SS}.")
        
    
    # ##########################
    # Header
    # ##########################
    out = bitarray.bitarray()
    # =======================
    # whole byte size[4B]
    # =======================
    # header[10B] + (badata[bit]/8)[B]
    wholebyte = int(10 + (len(badata))/8)
    out.extend(int2bin(wholebyte,32,signed=False))
    
    # =======================
    # start time [6B]
    # =======================
    out.extend(int2bin(yy//10,4,signed=False))
    out.extend(int2bin(yy%10,4,signed=False))
    out.extend(int2bin(mm//10,4,signed=False))
    out.extend(int2bin(mm%10,4,signed=False))
    out.extend(int2bin(dd//10,4,signed=False))
    out.extend(int2bin(dd%10,4,signed=False))
    out.extend(int2bin(HH//10,4,signed=False))
    out.extend(int2bin(HH%10,4,signed=False))
    out.extend(int2bin(MM//10,4,signed=False))
    out.extend(int2bin(MM%10,4,signed=False))
    out.extend(int2bin(SS//10,4,signed=False))
    out.extend(int2bin(SS%10,4,signed=False))
    
    # ##########################
    # Output
    # ##########################
    out.extend(badata)
    return out
    

def __satisfy_sample_size__(
    data: np.ndarray,
    sample_size: int,
    signed: bool = True,
    ):
    """
    データがサンプルサイズを満たしているか調べる．
    """
    if signed:
        if sample_size == 5:
            bitlim = 2**31
            if (
                -bitlim <= np.min(data)
                and np.max(data)<= bitlim-1
                ):
                return True
            else:
                return False
        else:
            bitlim = 2**31
            if (
                -bitlim <= data[0]
                and data[0] <= bitlim-1
                ):
                if sample_size == 0:
                    sample_size = 0.5
            
                bitlim = 2**(8*sample_size-1)
                _diff = data[1:] - data[:-1]
                if (
                    -bitlim <= np.min(_diff)
                    and np.max(_diff) <= bitlim-1
                    ):
                    return True
                else:
                    return False
            else:
                return False
    else:
        if sample_size == 5:
            # 4B (32bit)
            if np.max(data) < (2**32):
                return True
            else:
                return False
        else:
            if sample_size == 0:
                sample_size = 0.5
            
            # the first sample is 4B
            if data[0] < (2**32):
                # the rest samples
                _data = data[1:] - data[:-1]
                if np.max(_data) < (2**(sample_size*8)):
                    return True
                else:
                    return False
            else:
                return False

def __auto_sample_size__(
    data: np.ndarray,
):
    """
    Find the smallest sample size which satisfies the data.
    """
    for s in [0,1,2,3,4,5]:
        if __satisfy_sample_size__(data,s,signed=True):
            return s
    raise ValueError("No sample size satisfies the data.")

def __1ch2bin__(
    data:np.ndarray,
    fs:int,
    chnumber:int = 0x10,
    sample_size:int = None,
    force_make_int:bool = True,
    ) -> bitarray:
    """
    Return a byte string converted from input data array.
    samplesize 5 is supported by only win version > 3.
    (created 2024/09/21)
    
    Parameters
    ----------
    data: np.ndarray
        Input data array. Must be array of integers.
    fs: int
        Sampling frequency [Hz].
    chnumber: int
        Channel number in hexadecimal.
    sample_size: int
        Indicates size of each sample in byte and writing method of data.
        Takes value of 0,1,2,3,4,or5.
        0: 0.5 byte
        1: 1 byte
        2: 2 byte
        3: 3 byte
        4: 4 byte
        5: 4 byte [Recommended]
        The first sample is treated as 4 byte integer regardless to the sample size.
        Only samples after the second sample is converted into the above size (except 5).
        For 5, values of data is interpreted as amplitude, not as differential of amplitude from a previous step. [Supported by WIN version >= 3]
    
    Returns
    -------
    
    """
    # ##########################
    # Check input
    # ##########################
    if sample_size is None:
        sample_size = __auto_sample_size__(data)
        logger.debug(f"Auto sample size is set to {sample_size}.")
    
    
    if not np.issubdtype(data.dtype, np.integer):
        if force_make_int:
            data = data/np.max(abs(data[data>0])) * 0xFF
            data = data.astype(int)
        else:
            raise AssertionError(f"Input data type {data.dtype} must be integer.")
    
    if int(chnumber) < 0 or int(chnumber) > 0xFFFF:
        raise AssertionError(f"Channel number {chnumber} is out of range of 16-bit integer.")
    
    if not sample_size in [0,1,2,3,4,5]:
        raise AssertionError(f"Unexpected sample size {sample_size}! It should be either 0,1,2,3,4,or 5.")
    if int(fs)!=fs:
        raise AssertionError(f"Sampling frequency {fs} must be integer.")
    
    if len(data) > fs:
        raise AssertionError(f"1s data length {len(data)} is inconsistent to sampling frequency {fs}Hz.")
    # ##########################
    # Prepare output
    # ##########################
    out = bitarray.bitarray()
    
    # #####################
    # CHANNEL HEADER [4B]
    # #####################
    # ======================
    # ch number [2B]
    # ======================
    # write --------
    out.extend(
        int2bin(int(chnumber),16,signed=False)
    )
    # ======================
    # data size[0.5B], fs [1.5B]
    # ======================
    # write --------
    out.extend(
        int2bin(int(sample_size),4,signed=False)
    )
    out.extend(
        int2bin(int(fs),12,signed=False)
    )
    
    # #######################
    # data [4B] 
    # #######################
    # ======================
    # Convert data into byte strings 
    # ======================
    if sample_size == 5:
        _bin_data = intarray2bin(
            data,
            int(sample_size*8),
            signed=True,
            )
        out.extend(_bin_data)
        # for d in data:
        #     out.extend(
        #         int2bin(d,32,signed=True)
        #     )
    else:
        # sample_size = 0,1,2,3,4
        # First Sample -------------
        out.extend(
            bitarray.bitarray(
                "".join(int2bin(data[0],32,signed=True))
            )
        )
        # Rest Samples ------------
        if sample_size == 0:
            sample_size = 0.5
        
        if len(data) > 0:
            _data = data[1:] - data[:-1]
            _bin_data = intarray2bin(
                _data,
                int(sample_size*8),
                signed=True,
                )
            out.extend(
                bitarray.bitarray(
                    "".join(_bin_data)
                )
            )
            # for i in range(len(_bin_data)):
            #     out.extend(

            #     )
    
    # =======================
    # Check before return
    # =======================
    if sample_size==0.5 and len(out) % 8 != 0:
        out.extend('0'*4)
        
    if len(out) % 8 != 0:
        raise ValueError(f"Output data length {len(out)} is not aligned to 8-bit.")
    return out

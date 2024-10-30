"""
Module for reading WIN data (2024/09/14)

"""
#%%
import os
import numpy as np
# import xarray as xr
import pandas as pd
import datetime
from ....utils.log import logger
from ....utils.timehandler import yy2yyyy
from .parser import bit_parser
# from bitarray import bitarray

    
def __get_timerangelist__(
    fps:list[str],
):
    """
    複数ファイルの開始時刻と終了時刻の配列を取得する．
    """
    st = [None]*len(fps)
    et = [None]*len(fps)
    for i in range(len(fps)):
        logger.debug(f"Getting Time Range {i+1}/{len(fps)}")
        fp = fps[i]
        segments = bit_parser.__split1s__(fp)
        st[i] = bit_parser.__get_starttime__(segments[0])
        et[i] = bit_parser.__get_starttime__(segments[-1]) + datetime.timedelta(seconds=1)
    return st, et

def __read1file__(
    fp:str,
    chnumber:list[str] = None,
) -> pd.Series:
    """
    Read 1 file and return data.
    """
    # =======================
    # oepn and split into each 1s segments
    # =======================
    segments = bit_parser.__split1s__(fp)
    # =======================
    # convert into 1ch data
    # =======================
    # chlist = [None]*len(segments)
    # datalist = [None]*len(segments)
    datasr = [None]*len(segments)
    for i in range(len(segments)):
        ch, data = bit_parser.__split_1s_to_1ch__(
            segments[i],
            # chnumber = chnumber,
            )
        # chlist[i] = ch
        # datalist[i] = data
        
        datasr[i] = pd.Series(
            data,
            index = ch,
        )
    
    # concat all 1s sections -----------
    outdata = pd.concat(datasr, axis=1,ignore_index=True)
    
    # extract channel -----------
    if chnumber is not None:
        outdata = outdata.loc[chnumber]
    
    outdata = outdata.apply(lambda row: np.hstack(row.values), axis=1)
    
    # bit1ch_list = []
    # for i in range(len(segments)):
    #     logger.debug(f"Reading {i+1}/{len(segments)}")
    #     bit1ch = bit_parser.__split_1s_to_1ch__(
    #         segments[i],
    #         chnumber = chnumber,
    #         )
    #     bit1ch_list.append(bit1ch)
    # return segments
    # return chlist, datalist
    return outdata

def __readwin__(
    fp:list[str],
    chnumber:list[str] = None,
    targettime:datetime.datetime = None,
    beforesec:float = None,
    aftersec:float = None,
    filenameformat:str = None,
) -> pd.Series:
    """
    Load WIN file(s).
    """
    # =======================
    # CHECK
    # =======================
    if type(fp) == str:
        fp = [fp]
    logger.debug(f"Given {len(fp)} files.")
    # =======================
    # MAIN
    # =======================
    if targettime is None:
        # ----------------------
        # read whole data in fp 
        # ----------------------
        logger.debug(f"Loading...")
        
        if len(fp) == 1:
            datadf = __read1file__(
                fp[0],
                chnumber = chnumber,
                )
            return datadf
        else:
            # load each file -----------
            datadf_list = []
            for i in range(len(fp)):
                datadf = __read1file__(
                    fp[i],
                    chnumber = chnumber,
                    )
                datadf_list.append(datadf)
            
            # concat loaded files -----------
            _tmpdf = pd.concat(datadf_list, axis=1)
            # outdata = _tmpdf.apply(lambda row: np.hstack(row.values), axis=1)
            outdata = _tmpdf.apply(
                lambda row: np.hstack(pd.Series(row.values).T.drop_duplicates().values.T),
                axis=1
                )
            
            return outdata
    else:
        # ----------------------
        # extract data based on target time
        # ----------------------
        logger.info(f"Searching data around {targettime}...")
        # ......................
        # check
        # ......................
        if beforesec is None:
            raise ValueError("Beforesec must be given when targettime is given.")
        if aftersec is None:
            raise ValueError("Aftersec must be given when targettime is given.")
        
        if beforesec < 0:
            raise ValueError(f"Beforesec must be positive: {beforesec}")
        if aftersec < 0:
            raise ValueError(f"Aftersec must be positive: {aftersec}")
        # check start/end time and find index -----------
        tarstarttime = targettime - datetime.timedelta(seconds=beforesec)
        tarendtime = targettime + datetime.timedelta(seconds=aftersec)
        if tarstarttime >= tarendtime:
            raise ValueError(f"Start time is same or later than end time: start {tarstarttime}, end {tarendtime}")
        
        # ......................
        # get start/end time list
        # ......................
        if filenameformat is not None:
            logger.debug("Using filenameformat to get time range.")
            # faster method -----------
            stlist = [None]*len(fp)
            etlist = [None]*len(fp)
            for i in range(len(fp)):
                f = fp[i]
                _st = datetime.datetime.strptime(
                    os.path.basename(f),
                    filenameformat,
                    )
                stlist[i] = _st
            etlist[:-1] = stlist[1:]
            
            # last end time -----------
            lastseg = bit_parser.__split1s__(fp[-1])[-1]
            etlist[-1] = bit_parser.__get_starttime__(lastseg) + datetime.timedelta(seconds=1)
                
        else:
            logger.debug("Opening all data to get time range of the data")
            # ----------------------
            # get time range of each file
            # ----------------------
            stlist, etlist = __get_timerangelist__(fp)
            
        # ----------------------
        # check given target time
        # ----------------------
        if tarstarttime < min(stlist):
            logger.warning(
                f"{tarstarttime} < {min(stlist)}\n"
                f"Requested start time is earlier than the start time of the given files. "
                f"Start time is set to the that of the first file."
                )
            startidx = 0
        else:
            for i in range(len(fp)):
                if stlist[i] <= tarstarttime and tarstarttime < etlist[i]:
                    startidx = i
                    break
            
        
        if tarendtime > max(etlist):
            logger.warning(
                f"Requested end time is later than the end time of the given files."
                f"End time is set to the that of the last file."
                )
            endidx = len(fp) - 1
        else:
            for i in range(len(fp)):
                if stlist[i] <= tarendtime and tarendtime <= etlist[i]:
                    endidx = i
                    break
            logger.debug(f"fp: {fp[startidx:endidx+1]}")
            
        # ......................
        # read data
        # ......................
        outdata = __readwin__(
            fp[startidx:endidx+1],
            chnumber = chnumber,
            )
        # trim data -----------
        
        for i in range(len(outdata)):
            outdata.iloc[i] = outdata.iloc[i][:,
                (outdata.iloc[i][1,:] >= tarstarttime) & (outdata.iloc[i][1,:] < tarendtime)
            ]
        # outdata = outdata.apply(
        #     lambda row:  row[:, (row[1:] >= tarstarttime) & (row[1:] < tarendtime)],
        # # axis=1
        # )
        
        return outdata



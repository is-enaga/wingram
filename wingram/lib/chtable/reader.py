"""
- v0.3.0-a1
    - bug fix: 19列目以降のデータが読み込まれないバグを修正
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from bitarray import bitarray
from ...utils import *

def read_chtable(fp:str, encoding:str="utf-8"):
    """
    WINのチャネル表を読み込み，pandasのDataFrameで返す．
    「#」ではじまる行はコメント行として飛ばす．
    """
    idx = ["ch", "flag", "delay_time", "station", "component", "monitor_size", "ad_bit_size", "sensitivity", "unit", "natural_period", "damping", "ad_gain", "ad_bit_step", "lat", "lon", "elv", "p_correction", "s_correction", "note"]
    table = []
    max_row_len = 18
    with open(fp, 'r', encoding = encoding) as f:
        lines = f.readlines()
        for line in lines:
            logger.debug(line)
            line.strip()
            # SKIP COMMENT LINE and EMPTY LINE =====
            if line[0]=="#" or line=="\n":
                logger.debug(f"{line}:SKIP")
                continue
            
            # APPEND TABLE row ================
            row = line.split()
            
            # extend a row to has 18 columns
            if len(row) < 18:
                row.extend([None]*(18-len(row)))
            if len(row) == 19:
                max_row_len = 19
            elif len(row) > 19:
                row[19] = " ".join(row[19:])
                row = row[:19]
                max_row_len = 19
            # append
            table.append(row)
            logger.debug(f"{line}:WRITE")
            
    # Convert list to dataframe
    table = pd.DataFrame(table, columns=idx[:max_row_len])

    # Modify type
    table.fillna(
        "NaN",
        inplace=True
    )
    table["flag"] = pd.to_numeric(table["flag"], errors='coerce')
    table["delay"] = pd.to_numeric(table["delay"], errors='coerce')
    table["amp"] = pd.to_numeric(table["amp"], errors='coerce')
    table["bit"] = pd.to_numeric(table["bit"], errors='coerce')
    table["sense"] = pd.to_numeric(table["sense"], errors='coerce')
    table["nat_T"] = pd.to_numeric(table["nat_T"], errors='coerce')
    table["dump"] = pd.to_numeric(table["dump"], errors='coerce')
    table["ADamp"] = pd.to_numeric(table["ADamp"], errors='coerce')
    table["ADstep"] = pd.to_numeric(table["ADstep"], errors='coerce')
    table["lat"] = pd.to_numeric(table["lat"], errors='coerce')
    table["lon"] = pd.to_numeric(table["lon"], errors='coerce')
    table["elev"] = pd.to_numeric(table["elev"], errors='coerce')
    table["p_corr"] = pd.to_numeric(table["p_corr"], errors='coerce')
    table["s_corr"] = pd.to_numeric(table["s_corr"], errors='coerce')
    
    # table = table.astype(
    #     {
    #         'flag':int,
    #         'delay':int,
    #         'amp':int,
    #         'bit':int,
    #         'sense': float,
    #         'nat_T':float,
    #         'dump':float,
    #         'ADamp':float,
    #         'ADstep':float,
    #         'lat':float,
    #         'lon':float,
    #         'elev':float,
    #         'p_corr':float,
    #         's_corr':float,
    #     }
    # )
    # table[['flag','delay','amp','bit']] = table[['flag','delay','amp','bit']].astype(int)
    # table[['nat_T','dump','ADamp','ADstep','lat','lon','elev','p_corr','s_corr']] = table[['nat_T','dump','ADamp','ADstep','lat','lon','elev','p_corr','s_corr']].astype(float)
    
    return table

# =================================
# DAS Tabel Edit
# read_chtblで読んだdatが引数
# =================================
# --------------------------------
# MAIN
# -------------------------------
def interp_dastbl(
    dat: pd.DataFrame,
    ch_st = 200,
    ch_ed = 20000,
    ch_step = 1,
    ):
    logger.info("rename station code")
    # 20000chに書き換え
    rename_code(dat = dat, ch_st = ch_st, ch_ed = ch_ed)
    
    logger.info("put ch numbers in index")
    # インデックスにチャンネル番号を与える
    dat = rename_index(dat)
    
    logger.info("interpolate")
    # 補間
    dat = interp(dat, ch_step=ch_step)
    
    rename_code(dat = dat, ch_st = ch_st, ch_ed = ch_ed)
    
    return dat
    
# --------------------------------
# SUB
# --------------------------------
def rename_code(
    dat: pd.DataFrame,
    ch_st = 200,
    ch_ed = 20000,
):
    """
    DASのWINチャンネルテーブルの観測点コードを書き換える．
    篠原先生提供の50000chテーブルを20000chに書き換えるために作成．
    """
    ch = np.linspace(ch_st,ch_ed,dat.shape[0],endpoint=True).astype(int)
    # newch = [None]*dat.shape[0]
    newcode = [None]*dat.shape[0]
    for i in range(len(dat.ch)):
        # newch[i] = f"{i+1:04X}"
        newcode[i] = f"D.{ch[i]:0>5.0f}"
    # dat.ch = newch
    dat.code = newcode
    return dat

def rename_index(dat):
    """
    DASのcode名（「D.xxxxx」）をもとにpandasのインデックスをチャンネル番号に振りなおす．
    (以降の処理でチャンネル番号を扱うときにindexの値からチャンネル番号を参照できるようにするため)
    """
    idx = [None]*dat.shape[0]
    for i in range(len(idx)):
        idx[i] = int(dat.iloc[i].loc['code'].replace("D.",""))
    dat.index = idx
    return dat

def rename_ch(dat):
    """
    1はじまりの16進数のチャンネル番号を振りなおす
    """
    newch = [None]*dat.shape[0]
    for i in range(dat.shape[0]):
        newch[i] = f"{dat.index[i]:04X}"
        # newch[i] = f"{i+1:04X}"
    dat.ch = newch
    return dat


def interp(
    dat: pd.DataFrame,
    ch_step:int = 100,
):
    """
    ch_step間隔になるように補完する．
    
    ただし適切なch_stepを指定する必要がある．
    具体的には，補間後のチャンネルが等間隔の整数になるように，
    補間前のチャンネル間隔を割り切れる整数をch_stepとする必要がある．
    """
    # 
    chrange = dat.index[1] - dat.index[0]
    if chrange % ch_step != 0:
        logger.error("each ch should be integer!")
        return dat
    
    logger.debug(dat.index)
    # 拡張
    dat = dat.reindex(np.arange(dat.index[0], dat.index[-1]+1,ch_step))
    logger.debug(np.arange(dat.index[0], dat.index[-1]+1,ch_step).shape)
    logger.debug(dat.index)
    
    # 数値
    dat[['flag','delay','amp','bit','sense','nat_T','dump','ADamp','ADstep','lat', 'lon', 'elev']] = dat[['flag','delay','amp','bit','sense','nat_T','dump','ADamp','ADstep','lat', 'lon', 'elev']].interpolate(method='linear')
    
    # 16進数チャンネル番号
    dat = rename_ch(dat)

    # 文字
    dat = dat.ffill()
    
    return dat


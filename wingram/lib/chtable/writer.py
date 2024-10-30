import os
import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
# import datetime
# from bitarray import bitarray
from ...utils.log import logger
from ...utils import *


# ################################################
# WRITE TOOLS
# ################################################
def mk_chtbl(
    code:list[str],
    chnumber:list[int]=None,
    flag:list[int]=None,
    delay:list[int]=None,
    cmp:list[str]=None,
    monitor_amp:list[int]=None,
    bit_length:list[int]=None,
    sensitivity:list[float]=None,
    unit:list[str]=None,
    natural_period:list[float]=None,
    dump:list[float]=None,
    ADamp:list[float]=None,
    ADstep:list[float]=None,
    lat:list[float]=None,
    lon:list[float]=None,
    elev:list[float]=None,
    p_corr:list[float]=None,
    s_corr:list[float]=None,
    note:list[str]=None,
    # dat: np.ndarray,
    savedir = ".", savename = "ch.tbl",
    save = True,
    overwrite = False,
    **kwargs,
    ):
    """
    WINのチャネルテーブルファイルを作成・保存する．
    [4] code: list[str]
        観測点コード（観測点名）．10文字以内の任意の文字列．
    [1] chnumber: list[int]
        チャネル番号. 出力では2バイト16進数に直される．
    [2] flag: list[int]
        回収フラグ.
    [3] delay: list[int]
        回線遅延時間[ms].
    [5] cmp: list[str]
        成分名. 6文字以内の文字列．
    [6] monitor_amp: list[int]
        モニター波形の振幅縮率を示す指数（２の累乗数）
    [7] bit_length: list[int]
        AD変換時の量子化ビット数.
    [8] sensitivity: list[float]
        センサーの感度（V/入力振幅単位、入力振幅単位は[9]で示す）、実数でもよい
    [9] unit: list[str]
        [8]における入力振幅単位、MKS系で、変位は"m"、速度は"m/s"、加速度は"m/s/s"と書くこと
    [10] natural_period: list[float]
        震計の固有周期(s).
    [11] dump: list[float]
        地震計のダンピング定数
    [12] ADamp: list[float]
        センサー出力からA/D変換までの電圧増幅率(dB)
    [13] ADstep: list[float]
        A/D変換の１量子化ステップ幅(V)
    [14] lat: list[float]
        緯度
    [15] lon: list[float]
        経度
    [16] elev: list[float]
        海抜高度[m].
    [17] p_corr: list[float]
        P波到達時刻補正値[s].この値が観測値に足された後で震源計算される．
    [18] s_corr: list[float]
        S波到達時刻補正値[s].この値が観測値に足された後で震源計算される．
    [19] note: list[str]
        備考．任意の文字列．
    このうち[2],[3],[7],[10],[11]は、winでは使いませんが、 空白ではいけません。
    [14]〜[18]は観測点固有の値なので、１観測点に複数のチャネルがある 場合は、そのうちどれかの１チャネルのところに書いてあればいいです。
    
    dat: 各列にwintableの中身が入っている．
    """
    # ----------------------
    # check
    # ----------------------
    if type(code) == str:
        code = [code]
    stnnum = len(code)
    
            
    # None -> 初期値 -----------
    if chnumber is None:
        chnumber = np.arange(stnnum)
        logger.debug(f"chnumber is None. Set to {chnumber}")
    if flag is None:
        flag = [1] * stnnum
        logger.debug(f"flag is None. Set to {flag}")
    if delay is None:
        delay = [0] * stnnum
        logger.debug(f"delay is None. Set to {delay}")
    if cmp is None:
        cmp = ["-"] * stnnum
        logger.debug(f"cmp is None. Set to {cmp}")
    if monitor_amp is None:
        monitor_amp = [8] * stnnum
        logger.debug(f"monitor_amp is None. Set to {monitor_amp}")
    if bit_length is None:
        bit_length = [32] * stnnum
        logger.debug(f"bit_length is None. Set to {bit_length}")
    if sensitivity is None:
        sensitivity = [50.0] * stnnum
        logger.debug(f"sensitivity is None. Set to {sensitivity}")
    if unit is None:
        unit = ["_"] * stnnum
        logger.debug(f"unit is None. Set to {unit}")
    if natural_period is None:
        natural_period = [1] * stnnum
        logger.debug(f"natural_period is None. Set to {natural_period}")
    if dump is None:
        dump = [1] * stnnum
        logger.debug(f"dump is None. Set to {dump}")
    if ADamp is None:
        ADamp = [1] * stnnum
        logger.debug(f"ADamp is None. Set to {ADamp}")
    if ADstep is None:
        ADstep = [1] * stnnum
        logger.debug(f"ADstep is None. Set to {ADstep}")
    if lat is None:
        lat = [35.718361243868] * stnnum
        logger.debug(f"lat is None. Set to {lat}")
    if lon is None:
        lon = [139.76020144097657] * stnnum
        logger.debug(f"lon is None. Set to {lon}")
    if elev is None:
        elev = [0] * stnnum
        logger.debug(f"elev is None. Set to {elev}")
    if p_corr is None:
        p_corr = [0] * stnnum
        logger.debug(f"p_corr is None. Set to {p_corr}")
    if s_corr is None:
        s_corr = [0] * stnnum
        logger.debug(f"s_corr is None. Set to {s_corr}")
    if note is None:
        note = [""] * stnnum
        logger.debug(f"note is None. Set to {note}")
        
    args = [flag, delay, cmp, monitor_amp, bit_length,
        sensitivity, unit, natural_period, dump, ADamp, ADstep,
        lat, lon, elev, p_corr, s_corr, note]
    argstr = ["flag", "delay", "cmp", "monitor_amp", "bit_length",
        "sensitivity", "unit", "natural_period", "dump", "ADamp", "ADstep",
        "lat", "lon", "elev", "p_corr", "s_corr", "note"]
    
    # 単体ならリストに変換 -----------
    for i in range(len(args)):
        arg = args[i]
        if type(arg) == int or type(arg) == float or type(arg) == str:
            arg = [arg] * stnnum
            args[i] = arg
            logger.debug(f"arg {argstr[i]} is converted to list: {arg}")
    # 長さチェック -----------
    for i in range(len(args)):
        logger.debug(f"{argstr[i]}: {args[i]}")
        arg = args[i]
        if len(arg) != stnnum:
            raise ValueError(
                f"Length of args must be same as code ({stnnum}), "
                f"but {len(arg)} is given for {argstr[i]}."
                )
    # ----------------------
    # main
    # ----------------------
    dat = pd.DataFrame([chnumber, args[0], args[1], code]+ args[2:])
    text = ""
    
    if len(dat.shape) == 1 or (len(dat.shape)!=1 and dat.shape[0]==1):
        row = dat.values
            
        text +=  f"{row[0]:04X} {row[1]:1.0f}  {row[2]:4.0f}  {row[3]:10}  {row[4]:6}   {row[5]:.0f} {row[6]:.0f}     {row[7]:.1f} {row[8]}     {row[9]:.0f}  {row[10]:.0f}  {row[11]:.0f}  {row[12]:9.3E} {row[13]:9.6f} {row[14]:10.6f} {row[15]:<5.0f} {row[16]} {row[17]}"
        text += "\n"
    else:
        logger.debug(f"dat.shape: {dat.shape}")
        for i in range(dat.values.T.shape[0]):
            row = dat.values.T[i]
            for i in range(len(row)):
                logger.debug(f"row[{i}]: {row[i]} <{type(row[i])}>")

            text += f"{row[0]:04X} {row[1]:1.0f}  {row[2]:4.0f}  {row[3]:10}  {row[4]:6}   {row[5]:.0f} {row[6]:.0f}     {row[7]:.1f} {row[8]}     {row[9]:.0f}  {row[10]:.0f}  {row[11]:.0f}  {row[12]:9.3E} {row[13]:9.6f} {row[14]:10.6f} {row[15]:<5.0f} {row[16]} {row[17]}"
            text += "\n"
    
    # ---------------------------------
    # save
    # ---------------------------------
    if save:
        savefp = os.path.join(savedir, savename)
        if not os.path.exists(savedir):
            os.mkdir(savedir)
            
        if os.path.exists(savefp) and overwrite == False:
            logger.warning("File already exists and overwrite==False!: {savefp}")
        else:
            with open(savefp, 'w') as f:
                f.write(text)
            logger.info(f"Saved: {savefp}")

    return text

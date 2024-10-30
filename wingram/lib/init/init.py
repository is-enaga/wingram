import os
import numpy as np
import pandas as pd
import datetime
from io import StringIO
# from ...utils.logger import logger
from ...utils import *
from ..seis import *
# #########################################################################
# init: hypomhのinit
# #########################################################################
def mkinit(
    initlat: float = 0,
    initlon: float = 0,
    initdep: float = 0,
    unclat: float = 100.,
    unclon: float = 100.,
    uncdep: float = 30.,
    yy:int = 93,
    mm:int = 7,
    dd: int = 22,
    H: int = 12,
    M: int = 6,
    S: float = 2.162,
    sourcelat = None,
    sourcelon = None,
    sourcedep = None,
    sourcemag = None,
    calc_tt = False,
    savedir = ".",
    savename = None,
    save = False,
    ):
    """
    hypomhのinit（初期値）ファイルを作成する．
    
    --
    初期値のファイル。初期震源の緯度(度)、経度(度)、 深さ(km)を１行目に、
    それぞれの不確定さ(km)を２行目に書く。
    値はいずれも小数点付きで、各項目の幅は10桁ずつ。
    このファイルを指定しないと、構造ファイルに指定した値が使われる。
    
    --
    走時計算モード
        （calc_tt = Trueとする）
    ３行目として震源要素(年、月、日、時、分、秒、緯度、経度、深さ、M )を 適当に空白で区切って書いてください(" 93 7 22 12 6 2.162 34.76181 140.09901 60.004 2.0"など) 。
    
    See Also
    --------
    hypomh.f l.103-
    ```FORTRAN
            OPEN(12,FILE=FILE,STATUS='OLD')
            READ(12,100) ALAT00,ALNG00,DEPT00
            READ(12,100) ELAT00,ELNG00,EDPT00
    ......
    100 FORMAT(3F10.3)
    ```
    
    """
    
    
    # ========================================================================
    # start
    # ======================================================================
    text = ""
    # 1行目 初期位置
    # text += f"{initlat:3.5f}  {initlon:3.5f}  {initdep:.3f}\n"
    text += f"{initlat:<10.3f} {initlon:<10.3f} {initdep:<10.3f}\n"
    
    # 2行目 不確かさ[km]
    # text += f"{unclat:3.6f}  {unclon:3.6f}  {uncdep:.3f}\n"
    text += f"{unclat:<10.3f}{unclon:<10.3f}{uncdep:<10.3f}\n"

    # 3行目
    if calc_tt == True:
        if sourcelat is None or sourcelon is None or sourcedep is None or sourcemag is None:
            logger.warning(f"some of source parameters are not given! lat{sourcelat} lon{sourcelon} dep{sourcedep} mag{sourcedep}")
        
        text += f"{yy} {mm} {dd} {H} {M} {S} {sourcelat:3.5f} {sourcelon:3.5f} {sourcedep} {sourcemag}"

    if save:
        if not os.path.exists(savedir):
            os.mkdir(savedir)
        savefp = os.path.join(savedir, savename)
        logger.info(f"WRITING: {savefp}")
        with open(savefp, 'w') as f:
            f.write(text)

    return text

def seis2init(
    seisfp: str,
    initdep: float = 30,
    unclat: float = 100.,
    unclon: float = 100.,
    uncdep: float = 30.,
    savedir = ".",
    savename = None,
):
    seis = Seis()
    seis.read(seisfp)
    if savename is None:
        savename = os.path.basename(seisfp).replace(".seis", ".init")
    
    initstation = seis.arrivals[seis.arrivals.ptime==seis.arrivals.ptime.min()]
    
    if initstation.empty:
        initstation = seis.arrivals[seis.arrivals.stime==seis.arrivals.stime.min()]
        logger.warning(
            f"There is no P arrival in the seis file: {seisfp}"
            f"\n Set initial position to the first S arrived station: {initstation.stncode.iloc[0]}"
            )
        
    mkinit(
        initlat = initstation.lat.iloc[0],
        initlon = initstation.lon.iloc[0],
        initdep = initdep,
        unclat = unclat,
        unclon = unclon,
        uncdep = uncdep,
        savedir = savedir,
        savename = savename,
        save = True,
    )
    return

def jma2win4init(
    catalog: pd.DataFrame,
    save: bool = False,
    savedir: str = "init"
    ):
    """
    jmaイベントから走時計算用のinitファイルを作成する．
    
    df: pandas.DataFrame
        震源情報が入ったデータ．
        各要素の名前が[lat, lon, dep, mag]という名前である必要がある
    """
    
    for i in range(len(catalog)):
        logger.info(f"Processing: {i}/{len(catalog)-1}")
        
        if len(catalog) >1:
            event = catalog.iloc[i]
        else:
            event = catalog
            
        dt = event.datetime
        
        logger.debug("dt")
        
        text = mkinit(
            initlat = event.lat,
            initlon = event.lon,
            initdep = event.dep,
            # unclat = 0.,
            # unclon = 0.,
            # uncdep = 0.,
            yy = dt.year,
            mm = dt.month,
            dd = dt.day,
            H = dt.hour,
            M = dt.minute,
            S = float(dt.strftime("%S.%f")),
            sourcelat = event.lat,
            sourcelon = event.lon,
            sourcedep = event.dep,
            sourcemag = event.mag,
            calc_tt = True,
        )
        
    
        # ========================================================================
        # save
        # ======================================================================
        if save:
            if not os.path.exists(savedir):
                os.mkdir(savedir)
            fname = dt.strftime("%y%m%d-%H%M%S.%f")
            savefp = os.path.join(savedir, fname)
            logger.info(f"WRITING: {savefp}")
            with open(savefp, 'w') as f:
                f.write(text)
    return text


"""
Modules for handling final file of hypomh.

History
-------
- v0.2.0
    - remove conventional Final.read and replaced by Final.read2
    (2024/07/03)
    - comment out Final.write (2024/07/03)
    - enhance Final.read (2024/07/03)
        - read info of each station and std of O-C of P, S.

"""
import os
import numpy as np
import pandas as pd
import datetime
from io import StringIO
# from ...utils.logger import logger
from ...utils import *

def read_final(fp:str):
    _final = Final()
    _final.read(fp)
    return _final

def read_finals(fplist:list[str]):
    # SETTINGS >>>>>>>>>>>>>>>>
    cols = [
        "time",
        "lat",
        "lon",
        "dep_km",
        "mag",
        "diag",
        "laterror",
        "lonerror",
        "deperror",
        "cxx",
        "cxy",
        "cxz",
        "cyy",
        "cyz",
        "czz",
        "n_station",
        "model",
        "n_p",
        "n_s",
        "poc_std",
        "soc_std",
    ]
    # >>>>>>>>>>>>>>>>>>>>>>>>>
    time = []
    lat = []
    lon = []
    dep_km = []
    mag = []
    diag = []
    laterror = []
    lonerror = []
    deperror = []
    cxx = []
    cxy = []
    cxz = []
    cyy = []
    cyz = []
    czz = []
    n_station = []
    model = []
    n_p = []
    n_s = []
    poc_std = []
    soc_std = []
    for fp in fplist:
        final = read_final(fp)
        time.append(final.origintime)
        lat.append(final.lat)
        lon.append(final.lon)
        dep_km.append(final.dep_km)
        mag.append(final.mag)
        diag.append(final.diag)
        laterror.append(final.laterror)
        lonerror.append(final.lonerror)
        deperror.append(final.deperror)
        cxx.append(final.cxx)
        cxy.append(final.cxy)
        cxz.append(final.cxz)
        cyy.append(final.cyy)
        cyz.append(final.cyz)
        czz.append(final.czz)
        n_station.append(final.n_station)
        model.append(final.model)
        n_p.append(final.n_p)
        n_s.append(final.n_s)
        poc_std.append(final.poc_std)
        soc_std.append(final.soc_std)
    finals = pd.DataFrame(
        {
            "time":time,
            "lat":lat,
            "lon":lon,
            "dep_km":dep_km,
            "mag":mag,
            "diag":diag,
            "laterror":laterror,
            "lonerror":lonerror,
            "deperror":deperror,
            "cxx":cxx,
            "cxy":cxy,
            "cxz":cxz,
            "cyy":cyy,
            "cyz":cyz,
            "czz":czz,
            "n_station":n_station,
            "model":model,
            "n_p":n_p,
            "n_s":n_s,
            "poc_std":poc_std,
            "soc_std":soc_std,
        }
    )
    return finals

class Final:
    """
    handle final file of hypomh.
    
    Parameters
    ----------
    text : str
        Raw text from final file.
    origintime : datetime.datetime
        Origin time.
    lat : float
        Hypocenter latitude in degrees.
    lon : float
        Hypocenter longitude in degrees.
    dep_km : float
        Hypocenter depth in km.
        Downward is positive.
    mag : float
        Magnitude.
        Get np.nan if not calculated.
    diag : str
        Diagnosis by hypomh.
        `CONV`, `NOCN`, `DEEP`, `AIRF`
    cxx, cxy, ..., czz : float
        Covariance matrix.
    initlat, initlon, initdep : float
        Initial hypocenter.
    initlatunc, initlonunc, initdepunc : float
        Uncertainty of initial hypocenter.
    n_station : int
        Number of stations.
    model : str
        Velocity structure model.
    n_p, n_s, n_init : int
        Number of P, S, initial data.
        n_init is always 3.
    contrib_p, contrib_s, contrib_init : float
        Contribution of P, S, initial data.
    arrivals : pd.DataFrame
        Arrival information of each station.
    poc_std, soc_std : float
        Standard deviation of O-C of P, S.
        
    Exaple
    ----
    ```python
    fp = "fp/for/final"
    final = Final()
    final.read(fp)
    ```
    
    Official documentation of win (pickfile)
    ----------------------------------------
    １行目は震源時・緯度(度)、経度(度)、深さ(km)・マグニチュード、  
    ２行目は診断（"CONV"・"NOCN"・"DEEP"・"AIRF"ど）と結果の誤差 （秒および km単位）です。ただし震源時の誤差は常に０で意味がありません。  
    ３行目は誤差共分散行列の６つの成分で、東をx、南をy、下をzに とった km 単位の座標系で、Cxx,Cxy,Cxz,Cyy,Cyz,Czzの順です。 従って２行目の緯度・経度・深さの誤差の自乗が、それぞれ Cyy,Cxx,Czzに なっているはずです。  
    ４行目は与えた初期震源の位置およびその不確定さ で、緯度(度)・緯度の不確定さ(km)・経度(度)・経度の不確定さ(km)・ 深さ(km)・深さの不確定さ(km)です。  
    ５行目は左から、観測点数、速度構造 モデル名、P時刻データの数、S時刻データの数、初期値データの数（これは 初期震源の座標なので常に３）で、括弧内はそれぞれのデータからの寄与の 割合がパーセントで示されています（ただしhypomhの作者によると P,Sそれぞれのパーセント表示は問題があって、両者の和は信用できる、 とのこと）。  
    ６行目からは各観測点ごとの結果が観測点数だけあって、各行の内容は、 左から、観測点コード・P極性・震央距離(km)・観測点方位（北から東回り (度））・射出角（下から(度））・入射角（下から(度））・観測点補正後の P時刻(s)・P精度(s)・P時刻のO-C(s)・観測点補正後のS時刻(s)・S精度(s)・ S時刻のO-C(s)・最大振幅(m/s)・マグニチュードです。ただし、最大振幅 データがなくてF-P時間データがある場合には、最大振幅の代わりに F-P時間(s)が表示されます。F-P時間の場合は一般に値が１以上になります ので、値からこの判別は容易です。マグニチュードは、最大振幅データがある 場合は渡辺(1971)の式を、F-P時間データしかない場合は津村(1967)の式を、 それぞれ使って求められていて、値"9.9"はマグニチュード未決定の意味です。
    最後の行は、P時刻のO-CとS時刻のO-Cのそれぞれの標準偏差(s)です。 震源がよく決まった場合は、各観測点のO-C時間が精度と同程度以下に なっているはずです。  
    
    """
    text: str
    origintime:datetime.datetime
    lat:float
    lon:float
    dep_km:float
    mag:float
    diag:str
    cxx:float
    cxy:float
    cyy:float
    cyz:float
    czz:float
    cov:np.ndarray
    
    diag:str
    laterror:float
    lonerror:float
    deperror:float
    
    initlat:float
    initlatunc:float
    initlon:float
    initlonunc:float
    initdep:float
    initdepunc:float
    
    n_station:int
    model:str
    n_p:int
    contrib_p:float
    n_s:int
    contrib_s:float
    n_init:int
    contrib_init:float
    
    arrivals:pd.DataFrame
    poc_std:float
    soc_std:float
    
    def __init__(self):
        """
        generate Final object.
        """
        return
    
    # def write(
    #     self,
    #     outdir:str=None,
    #     outname:str=None,
    #     overwirte:bool = False,
    #     ):
        
    #     # =======================
    #     # prepare and check savefp
    #     # =======================
    #     if outdir is None:
    #         if hasattr(self, "fp"):
    #             outdir = os.path.dirname(self.fp)
    #     if outname is None:
    #         if hasattr(self, "fp"):
    #             outname = os.path.basename(self.fp)
                
    #     outfp = os.path.join(outdir, outname)
        
    #     if os.path.exists(outfp) and not overwirte:
    #         raise FileExistsError(f"File already exists: {outfp}")
            
    #     # =======================
    #     # check outdir
    #     # =======================
    #     if not os.path.exists(outdir):
    #         logger.info(f"Make directory: {outdir}")
    #         os.makedirs(outdir)
        
    #     # =======================
    #     # write
    #     # =======================
    #     outtxt = "\n".join(self.lines) + "\n"
    #     with open(outfp, 'w') as f:
    #         f.write(outtxt)
    #     logger.info(f"WRITTEN: {outfp}")
    
    def read(self, fp:str):
        """
        read final file by hypomh.
        Parameters
        ----------
        fp : str
            file path for final file.
        
        See Also
        --------
        hypomh.f l.237-
        ```FORTRAN
        2100 FORMAT('***** FINAL RESULTS *****')
            WRITE( 6,2200) IYR,MNT,IDY,IHR,MIN,COT,ALATF,ALNGF,XM1(3)
            *              ,AMAG
            WRITE(22,2200) IYR,MNT,IDY,IHR,MIN,COT,ALATF,ALNGF,XM1(3)
            *              ,AMAG
            WRITE(21,2200) IYR,MNT,IDY,IHR,MIN,COT,ALATF,ALNGF,XM1(3)
            *              ,AMAG
            WRITE(22,2210) DIAG,EOT,EX1(2),EX1(1),EX1(3)
            WRITE(21,2210) DIAG,EOT,EX1(2),EX1(1),EX1(3)
            WRITE( 6,2210) DIAG,EOT,EX1(2),EX1(1),EX1(3)
            WRITE(22,2220) H(1,1),-H(1,2),H(1,3),H(2,2),-H(2,3),H(3,3)
            WRITE(21,2220) H(1,1),-H(1,2),H(1,3),H(2,2),-H(2,3),H(3,3)
            WRITE( 6,2220) H(1,1),-H(1,2),H(1,3),H(2,2),-H(2,3),H(3,3)
            WRITE(22,2230) ALATI,EX0(2),ALNGI,EX0(1),XM0(3),EX0(3)
            WRITE(21,2230) ALATI,EX0(2),ALNGI,EX0(1),XM0(3),EX0(3)
            WRITE( 6,2230) ALATI,EX0(2),ALNGI,EX0(1),XM0(3),EX0(3)
            WRITE(22,2240) ND,VST,NPD,RSL(1),NSD,RSL(2),NPR,RSL(3)
            WRITE(21,2240) ND,VST,NPD,RSL(1),NSD,RSL(2),NPR,RSL(3)
            WRITE( 6,2240) ND,VST,NPD,RSL(1),NSD,RSL(2),NPR,RSL(3)
        ......
        2200 FORMAT(3I3.2,3X,2I3,F8.3,2F11.5,    F8.3,F6.1)
        2210 FORMAT(3X,A4,11X, F8.3,2(F9.3,2X),F8.3)
        C 2220 FORMAT(2(F8.3,1X),F8.3,2(F9.3,2X),F8.3)
        2220 FORMAT(6F10.3)
        2230 FORMAT(12X,3(F7.3,1X,F5.1,1X))
        2240 FORMAT(2X,I3,1X,A4,1X,3(I3,1X,'(',F5.1,'%',1X,')',1X))
        ```
        """
        # ==================
        # READ
        # ==================
        self.fp = fp
        with open(fp, 'r') as f:
            # _lines = f.readlines()
            self.text = f.read()
        
        # split into lines
        _lines = self.text.split("\n")
        
        # ================
        # CHECK
        # ================
        if len(_lines) < 5:
            logger.error(f"ERROR! Given file does not have expected number of lines: {fp}")
            self.origintime = np.nan
            self.lat, self.lon, self.dep_km = np.nan, np.nan, np.nan
            self.mag = np.nan
            self.cxx = np.nan
            self.cxy = np.nan
            self.cyy = np.nan
            self.cyz = np.nan
            self.czz = np.nan
            self.cov = np.nan
            self.diag = np.nan
            self.laterror = np.nan
            self.lonerror = np.nan
            self.deperror = np.nan
            return

        # =================
        # Parse text
        # =================
        # ------------------
        # row 1: origin time, hypocenter, magnitude
        # ------------------
        # .................
        # origin time
        # .................
        hypo = _lines[0]
        
        if hypo[18:26] != "********":
            # year -------------
            _yy = int(hypo[1:3])
            _yyyy = yy2yyyy(_yy)
                
            # second -------------
            _sec = float(hypo[18:26])
            # tmp datetime (yyyy,...,mm)-------
            self.origintime = (
                datetime.datetime(
                    int(_yyyy),
                    int(hypo[4:6]),
                    int(hypo[7:9]),
                    int(hypo[13:15]),
                    int(hypo[16:18]),
                )
                + datetime.timedelta(
                    seconds = _sec
                )
            )
            
        else: # if seconds is unreadable -----------
            self.datetime = np.nan
        
        # ..............
        # hypocenter
        # ..............
        self.lat = float(hypo[26:37]) # F11.5
        self.lon = float(hypo[37:48]) # F11.5
        self.dep_km = float(hypo[48:56]) # F8.3
        
        # ..............
        # magnitude
        # ..............
        self.mag = float(hypo[56:]) # F6.1
        if self.mag == 9.9:
            self.mag = np.nan
        
        # --------------
        # row2: CONV, errors
        # --------------
        qual = _lines[1]
        # classification -----------
        self.diag = qual[3:7]
        
        # error -----------
        self.laterror = float(qual[28:37])
        self.lonerror = float(qual[38:48])
        self.deperror = float(qual[48:56])
        
        # --------------
        # row3: Covariance matrix. Cxx, Cxy, ..., Czz
        # --------------
        cov = np.array(_lines[2].split()).astype(float)
        self.cxx = cov[0]
        self.cxy = cov[1]
        self.cxz = cov[2]
        self.cyy = cov[3]
        self.cyz = cov[4]
        self.czz = cov[5]
        self.cov = cov
        
        # ----------------------
        # row4: initial hypocenter
        # ----------------------
        init = _lines[3]
        # 12X
        self.initlat = float(init[12:19]) # F7.3 X1
        self.initlatunc = float(init[20:25]) # F5.1 X1
        self.initlon = float(init[26:33]) # F7.3 X1
        self.initlonunc = float(init[34:39]) # F5.1 X1
        self.initdep = float(init[40:47]) # F7.3 X1
        self.initdepunc = float(init[48:53]) # F5.1 X1
        
        # ----------------------
        # row5: number of stations, model, npd, nsd, npr
        # ----------------------
        info = _lines[4]
        # 2X
        self.n_station = int(info[2:5]) # I3 X1
        self.model = info[6:10] # A4 X1
        self.n_p = int(info[11:14]) # I3 X1
        self.contrib_p = float(info[16:21]) # (F5.1 % X1 ) X1
        self.n_s = int(info[25:28]) # I3 X1
        self.contrib_s = float(info[30:35]) # (F5.1 % X1 ) X1
        self.n_init = int(info[39:42]) # I3 X1
        self.contrib_init = float(info[44:49]) # (F5.1 % X1 ) X1
        
        # ----------------------
        # row6: station results
        # ----------------------
        # SETTINGS >>>>>>>>>>>>>>>>
        cols = [
            "code",
            "polarity",
            "distance_km",
            "azimuth",
            "takeoff",
            "incident",
            "ptime",
            "punc",
            "poc",
            "stime",
            "sunc",
            "soc",
            "amp",
            "mag",
        ]
        # >>>>>>>>>>>>>>>>>>>>>>>>>
        picks = _lines[5:-2]
        code = []
        polarity = []
        distance_km = []
        azimuth = []
        takeoff = []
        incident = []
        ptime = []
        punc = []
        poc = []
        stime = []
        sunc = []
        soc = []
        amp = []
        mag = []
        for i in range(len(picks)):
            pick = picks[i]
            code.append(pick[0:10])# A10 X1
            polarity.append(pick[11])# A2
            distance_km.append(float(pick[13:21]))# F8.3
            azimuth.append(float(pick[21:27]))# F6.1
            takeoff.append(float(pick[27:33]))# F6.1
            incident.append(float(pick[33:39]))# F6.1
            ptime.append(float(pick[39:46]))# F7.3
            punc.append(float(pick[46:52]))# F6.3
            poc.append(float(pick[52:59]))# F7.3
            stime.append(float(pick[59:66]))# F7.3
            sunc.append(float(pick[66:72]))# F6.3
            soc.append(float(pick[72:79]))# F7.3
            amp.append(float(pick[79:89]))# E10.3
            mag.append(float(pick[89:94]))# F5.1
        self.arrivals = pd.DataFrame(
            {
                "code":code,
                "polarity":polarity,
                "distance_km":distance_km,
                "azimuth":azimuth,
                "takeoff":takeoff,
                "incident":incident,
                "ptime":ptime,
                "punc":punc,
                "poc":poc,
                "stime":stime,
                "sunc":sunc,
                "soc":soc,
                "amp":amp,
                "mag":mag,
            }
        )
        # ----------------------
        # row7: standard deviation of O-C
        # ----------------------
        self.poc_std = float(_lines[-2][52:59]) # F7.3
        self.soc_std = float(_lines[-2][72:79]) # F7.3
        
        return 
    
    def xyellipse(self):
        azimuth, a, b = cov2ellipse(self.cxx,self.cyy,-1*self.cxy)
        return azimuth,a,b
    
    def yzellipse(self):
        azimuth, a, b = cov2ellipse(self.cyy,self.czz,-1*self.cyz)
        return azimuth,a,b
    
    def xzellipse(self):
        azimuth, a, b = cov2ellipse(self.cxx,self.czz,-1*self.cxz)
        return azimuth,a,b


# ##########################
# HELPER for Final
# ##########################

def cov2ellipse(cxx,cyy,cxy):
    cov = np.array(
        [[cxx,cxy],
         [cxy,cyy]]
    )
    
    print(np.linalg.eig(cov))
    eigval, eigvec = np.linalg.eig(cov)

    # eigval = np.abs(np.array(eigval))
    if eigval[0] >= eigval[1]:
        a = np.sqrt(eigval[0]) # major
        b = np.sqrt(eigval[1]) # minor
        avec = eigvec[:,0] # major
    else:
        a = np.sqrt(eigval[1])
        b = np.sqrt(eigval[0])
        avec = eigvec[:,1]
    
    azimuth = np.rad2deg(np.arctan2(avec[1],avec[0]))
    if azimuth < 0:
        azimuth += 360
    if azimuth > 180:
        azimuth -= 180
    return azimuth,a,b
    
# 
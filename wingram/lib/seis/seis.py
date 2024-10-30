"""
Module for seis file of hypomh, a file about arrival time picks.
Future Update
-------------
- v0.2.1
    - remove mkseis
    
History
-------
- v0.2.0
    - add WIN
    - remove ``read_seis``: because it was under editing but now available with Seis.
    - add Seis
    - move ``mkseis`` to Seis
        ``mkseis`` is now a static method of class ``Seis``.
        When use ``mkseis``, use ``Seis.make``.
    - edit Final
        renew read
    - bug fix
        conversion from yy to yyyy:
            yyyy = 1000 + yy -> 1"9"00 + yy
        fatal error in pnd2seis:
            second was contained in reftime.
            -> set seconds=0  
    - v0.2.0-a3 2024/06/29
        - change parameter name in Seis.make.(2024/06/27)
            stnelv_m -> stnelv_m
        - enhance Seis.make 2024/06/29
            None or np.nan for ptime and stime is now acceptable
            when P or S arrival is absent.
        - change Seis.make 2024/06/29
            savefp is now splited into savedir and savename.
        - enhance Seis.read 2024/06/29
            io.StringIO is acceptable for input "fp", 
            when directly read a text of seis file.
        - add Seis.read_seis 2024/06/29
    - v0.2.0-a4 2024/8/13
        - bug fix: Seis.__add__
            Solved the problem that self.reftime was not changed when self.reftime > other.reftime, 
"""
import os
import re
import numpy as np
import pandas as pd
import datetime
from io import StringIO
# from ...utils.logger import logger
from ...utils import *
# SETTINGS >>>>>>>>>>>>>>>>
# columns of the "arrivals" -----------
_COLS = [
    "stncode",
    "polarity",
    "ptime",
    "pcertainty",
    "stime",
    "scertainty",
    "fptime",
    "maxamp",
    "lat",
    "lon",
    "elev",
    "pcorrection",
    "scorrection",
    ]
_COLTYPES = {
    'stncode':str,
    'polarity':str,
    'ptime':float,
    'pcertainty':float,
    'stime':float,
    'scertainty':float,
    'fptime':float,
    'maxamp':float,
    'lat':float,
    'lon':float,
    'elev':float,
    'pcorrection':float,
    'scorrection':float,
}
# >>>>>>>>>>>>>>>>>>>>>>>>>

# #########################################################################
# seis
# #########################################################################
def mkseis(
    refyy: int,
    refmm: int,
    refdd: int,
    refHH: int,
    refMM: int,
    stnlat: list,
    stnlon: list,
    stnelv_m: list,
    stncode: list,
    polarity: list = [],
    ptime: list = [],
    pcert: list = [],
    stime: list = [],
    scert: list = [],
    fptime: list = [],
    maxamp: list = [],
    pcorrection: list = [],
    scorrection: list = [],
    savefp:str = [],
    save = False,
    ):
    """
    Old version of Seis.make and had moved to Seis.make.
    Support had stopped after v0.1.2.
    Will be removed in v0.2.1.
    """
    # ========================================================================
    # start
    # ======================================================================
    nrow = len(stnlat)
    
    if len(polarity) == 0:
        polarity = ["."]*nrow
    
    if len(ptime) == 0:
        ptime = [0]*nrow
    if len(pcert) == 0:
        pcert = [0]*nrow
    if len(stime) == 0:
        stime = [0]*nrow
    if len(scert) == 0:
        scert = [0]*nrow
    
    if len(fptime) == 0:
        fptime = [0]*nrow
    if len(maxamp) == 0:
        maxamp = [0]*nrow
    if len(pcorrection) == 0:
        pcorrection = [0]*nrow
    if len(scorrection) == 0:
        scorrection = [0]*nrow
    
    # ----------------------
    # station correction
    # ----------------------
    pcorrection = pd.Series(pcorrection).astype(float)
    scorrection = pd.Series(scorrection).astype(float)
    pcorrection.replace(np.nan,0,inplace=True)
    scorrection.replace(np.nan,0,inplace=True)
    
    _pcorrection = pcorrection.copy().astype(str)
    _scorrection = scorrection.copy().astype(str)
    for i in range(nrow):
        if pcorrection.iloc[i] != 0:
            _pcorrection.iloc[i] = f"{pcorrection.iloc[i]:>7.3f}"
        else:
            _pcorrection.iloc[i] = " "*7
        if scorrection.iloc[i] != 0:
            _scorrection.iloc[i] = f"{scorrection.iloc[i]:>7.3f}"
        else:
            _scorrection.iloc[i] = " "*7
        
        if _pcorrection.iloc[i] == " "*7 and _scorrection.iloc[i] == " "*7:
            _pcorrection.iloc[i] = ""
            _scorrection.iloc[i] = ""
            
    # =======================
    # MAIN
    # =======================
    text = ""
    
    # 1行目
    now = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
    text += f"{str(refyy)[-2:]}/{refmm:02.0f}/{refdd:02.0f} {refHH:02.0f}:{refMM:02.0f}                   {now}\n"

    # 2行目
    for i in range(nrow):
        text += f"{stncode[i]:<10} {polarity[i]:1}{ptime[i]:>8.3f}{pcert[i]:>6.3f}{stime[i]:>8.3f}{scert[i]:>6.3f}{fptime[i]:>6.1f}{maxamp[i]:9.2e}{stnlat[i]:11.5f}{stnlon[i]:11.5f}{stnelv_m[i]:>7.0f}{_pcorrection.iloc[i]}{_scorrection.iloc[i]}"
        text += '\n'
    
    if save:
        if savefp != None:
            with open(savefp,'w') as f:
                f.write(text)
                logger.info(f"SAVED: {savefp}")
        else:
            logger.warning(f"NOT SAVED: savefp is None!")
    return text


def jma2win4seis(
    catalog,
    tbl,
    save = False,
    savedir = "seis",
    ):
    """
    jmaのカタログとdasのチャネルテーブルから走時計算用のseisファイルを作る．
    """
    for i in range(len(catalog)):
        logger.info(f"Processing: {i}/{len(catalog)-1}")
        if len(catalog) >1:
            dt = catalog.datetime[i]
        else:
            dt = catalog.datetime
        logger.debug("dt")
        
        text = Seis.make(
            refyy = int(dt.strftime("%y")),
            refmm = int(dt.strftime("%m")),
            refdd = int(dt.strftime("%d")),
            refHH = int(dt.strftime("%H")),
            refMM = int(dt.strftime("%M")),
            stnlat = tbl.lat.values,
            stnlon = tbl.lon.values,
            stnelv_m = tbl.elev.values,
            stncode = tbl.code.values,
            # polarity: list = None,
            # ptime: list = None,
            # pcert: list = None,
            # stime: list = None,
            # scert: list = None,
            # fptime: list = None,
            # maxamp: list = None,
            # stncorr: list = None,
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


class Seis:
    """
    Class for seis file of win.
    Contains reference time and picked arrival times.
    If no pick, the arrival time is set to 0.
    
    .. versionadded:: 0.2.0
    
    Attributes
    ----------
    reftime:datetime.datetime
        A reference time of arrival times for line 1 of seis file.
    arrivals:pd.DataFrame
        A table of stations and arrival times for line >= 2 of seis file.
        The table should have columns below:
            - stncode: str
                Station code.
            - polarity: str
                Polarity of P wave.
                If no data, should be set to ".".
            - ptime: float
                Arrival time of P wave.
                Defined as seconds from ``reftime``.
            - pcert: float
                Certainty of arrival time of P wave .
            - stime: float
                Arrival time of S wave.
            - scert: float
                Certainty of arrival time of S wave.
            - fptime: float
                F-P time.
            - maxamp: float
                Maximum amplitude.
            - stnlat: float
                Latitude of station.
            - stnlon: float
                Longitude of station.
            - stnelv_m: float
                Elevation of station.
            - pcorrection: float
                Correction of P wave.
            - scorrection: float
                Correction of S wave.
    
    See Also
    --------
    - WIN System Official documentation
        <https://wwweic.eri.u-tokyo.ac.jp/WIN/man.ja/pickfile.html>
    
            seis
            到着時刻と観測点座標のデータファイル。 win の験測情報ファイル（pickファイル）中では、 "#s"で始まる部分から"#s"を取り除いたもの。フィルタ seis(1W) で 作れる。フォーマットは pickfile(1W)参照。
            
            99/11/09 06:46                   99/11/10 18:26:03
            ASO        D   6.854 0.015   0.000 0.000  43.9 1.77e-06   36.64934  139.45970    720
            NIK        U   6.884 0.006   0.000 0.000   0.0 6.84e-06   36.62144  139.49072   1310
            KBH        U   6.963 0.006   0.000 0.000  16.9 1.28e-06   36.65450  139.52824    750
            KRO        U   7.043 0.006   0.000 0.000   0.0 6.89e-07   36.68685  139.49794    865
            
            １行目は２行目以降の秒単位の到着時刻データの基準になる年〜分、および 右側にこのファイル（hypomhへの入力ファイル）を作った時刻が入ります。
            ２行目からは各行が１つの観測点の験測データで、左から、観測点コード、 P初動極性（データなしは "."）、P時刻(s)、P精度(s)、S時刻(s)、S精度(s)、 F-P時間(s)、最大振幅(m/sのときのみ書きだされる)、観測点緯度(度)、 経度(度)、高度(m)、Pの観測点補正(s)、Sの観測点補正(s)です。 PとSの観測点補正は、この値が到着時刻に加えらるもので、０のときには 省略されます。最後に空行（"#s"のみの行）が１行あります。
    
        走時モード
            PとSの到着時刻データをすべてゼロにしてください。
    
    - hypomh.f line ~572-578
                READ(13,1300,END=40) IYR,MNT,IDY,IHR,MIN
           1300 FORMAT(5(I2,1X))
                IF(NERQ.EQ.-1) RETURN
                I=1
              2 READ(13,1310,END=4) SA1(I),POLA1(I),PT1(I),PE1(I),ST1(I),SE1(I),
                1XT,AMP(I),ALAT(I),ALNG(I),IAHGT,STCP(I),STCS(I)
           1310 FORMAT(A10,1X,A1,2(F8.3,F6.3),F6.1,E9.2,2F11.5,I7,2F7.3)
    """

    def __init__(
        self,
        reftime:datetime.datetime=None,
        arrivals:pd.DataFrame=None,
        ):
        self.fp = None
        self.reftime = reftime
        self.arrivals = arrivals
        return
    
    def __str__(self):
        """
        Return text for seis file.
        """
        # =======================
        # check existence of data for writing
        # =======================
        if not hasattr(self, "reftime") or self.reftime is None:
            raise AttributeError("No reftime data. self.reftime is required.")
        if not hasattr(self, "arrivals") or self.arrivals is None:
            raise AttributeError("No arrival data. self.arrivals is required.")
        
        # =======================
        # np.nan to 0
        # =======================
        _ptime = np.nan_to_num(self.arrivals.ptime.values, nan=0)
        _stime = np.nan_to_num(self.arrivals.stime.values, nan=0)
        _pcert = np.nan_to_num(self.arrivals.pcertainty.values, nan=0)
        _scert = np.nan_to_num(self.arrivals.scertainty.values, nan=0)
        
        # =======================
        # MAIN
        # =======================
        ret = self.make(
            refyy = self.reftime.year,
            refmm = self.reftime.month,
            refdd = self.reftime.day,
            refHH = self.reftime.hour,
            refMM = self.reftime.minute,
            stnlat = self.arrivals.lat.values,
            stnlon = self.arrivals.lon.values,
            stnelv_m = self.arrivals.elev.values,
            stncode = self.arrivals.stncode.values,
            ptime = _ptime,
            pcert = _pcert,
            stime = _stime,
            scert = _scert,
            maxamp = self.arrivals.maxamp.values,
            pcorrection = self.arrivals.pcorrection.values,
            scorrection = self.arrivals.scorrection.values,
            # savefp = outfp,
            save = False,
            )
        return ret
    
    def __add__(self,other):
        """
        Concat two Seis objects.
        Reference time will be set to the min of two reference times.
        """
        if isinstance(other,Seis):
            if self.reftime != other.reftime:
                reftime = min(self.reftime, other.reftime)
                if self.reftime > other.reftime:
                    self.change_reftime(reftime)
                else:
                    other.change_reftime(reftime)
            else:
                reftime = self.reftime
            
            arrivals = pd.concat(
                [self.arrivals, other.arrivals],
                axis=0,
                )
            ret = Seis(reftime=self.reftime,arrivals=arrivals)
            ret.change_reftime(reftime)
            return ret
        else:
            return NotImplemented
        
    def __getitem__(self, index):
        """
        Return a Seis object with given rows.
        """
        fp = self.fp
        reftime = self.reftime
        if isinstance(index, int):
            if index == -1:
                arrivals = self.arrivals.iloc[-1:]
            else:
                arrivals = self.arrivals.iloc[index:index+1]
        else:
            arrivals = self.arrivals.iloc[index]
        out = Seis(reftime=reftime, arrivals=arrivals)
        out.reftime = reftime
        return out
    
    def __len__(self):
        return len(self.arrivals)
    
    def read(self,fp:str):
        """
        read a seis file of win.
        reference time and arrival picks are stored in self.reftime and self.arrivals.
        
        Parameters
        ----------
        fp:str or StringIO
            File path to seis file.
            StringIO of the text of seis file is also acceptable.
        """
        # load -----------
        if isinstance(fp, StringIO):
            _txt = fp.getvalue()
            _l = _txt.split("\n")
        else:
            with open(fp, 'r') as f:
                _txt = f.read()
            _l = _txt.split("\n")
        
        # When the input is pick file -----------
        if re.search(r'^#s', _txt, re.MULTILINE):
            logger.info("Reading pick file: Only lines start with '#s' are read.")
            _l = [line.lstrip("#s ") for line in _l if line.startswith("#s")]
        
        
        # reference time -----------
        yy = int(_l[0][0:2])
        mm = int(_l[0][3:5])
        dd = int(_l[0][6:8])
        HH = int(_l[0][9:11])
        MM = int(_l[0][12:14])
        yyyy = yy2yyyy(yy)
        
        # arrival pick -----------
        table = []
        for line in _l[1:-1]:
            if line=="":
                continue
            # when no p,s correction -----------
            if len(line) < 98:
                line = line + " "*(98-len(line))
            
            # ----------------------
            # convert
            # ----------------------
            row = [None]*13
            row[0] = line[0:10]
            row[1] = line[11]
            row[2] = line[12:20]
            row[3] = line[20:26]
            row[4] = line[26:34]
            row[5] = line[34:40]
            row[6] = line[40:46]
            row[7] = line[46:55]
            row[8] = line[55:66]
            row[9] = line[66:77]
            row[10] = line[77:84]
            row[11] = line[84:91]
            row[12] = line[91:98]
            
            table.append(row)   
        
        # widths = [10, 1, 1, 8, 6, 8, 6, 6, 9, 11, 11, 7, 7, 7]
        # cols = ["stncode","polarity","ptime","pcertainty","stime","scertainty","fptime","maxamp","lat","lon","elev","pcorrection","scorrection"]
        
        arrivals = pd.DataFrame(
            table,
            columns = _COLS,
            )
        
        # Replace empty correction values -----------
        arrivals['pcorrection'] = arrivals['pcorrection'].replace(' '*7, '0')
        arrivals['scorrection'] = arrivals['scorrection'].replace(' '*7, '0')
        
        # Change type -----------
        dtypes = _COLTYPES
        arrivals = arrivals.astype(dtypes)
        
        # Replace empty arrival times -----------
        arrivals['ptime'] = arrivals['ptime'].replace(0, np.nan)
        arrivals['stime'] = arrivals['stime'].replace(0, np.nan)
        arrivals['pcertainty'] = arrivals['pcertainty'].replace(0, np.nan)
        arrivals['scertainty'] = arrivals['scertainty'].replace(0, np.nan)
        arrivals['pcorrection'] = arrivals['pcorrection'].replace(0, np.nan)
        arrivals['scorrection'] = arrivals['scorrection'].replace(0, np.nan)

        self.fp = fp
        self.reftime = datetime.datetime(yyyy,mm,dd,HH,MM)
        self.arrivals = arrivals

        return self
    
    def write(
        self,
        outdir:str,
        outname:str=None,
        overwrite:bool=False,
        ):
        """
        Convert Seis into text and save as a seis file.
        
        Parameters
        ----------
        outdir: str
            Directory to save the seis file.
        outname: str
            File name of the seis file.
            If None, the basename of self.fp is used.
        overwrite: bool
            If True, allow to overwrite the file with same file path.
        """
        # =======================
        # check existence of data for writing
        # =======================
        if not hasattr(self, "reftime"):
            raise AttributeError("No reftime data. self.reftime is required.")
        if not hasattr(self, "arrivals"):
            raise AttributeError("No arrival data. self.arrivals is required.")
        
        # =======================
        # prepare and check savefp
        # =======================
        if outname is None:
            if hasattr(self, "fp"):
                outname = os.path.basename(self.fp)
                
        if not os.path.exists(outdir):
            logger.info(f"Make directory: {outdir}")
            os.makedirs(outdir)
            
        outfp = os.path.join(outdir, outname)
        
        if os.path.exists(outfp) and not overwrite:
            raise FileExistsError(f"File already exists: {outfp}")
        
        with open(outfp, 'w') as f:
            f.write(str(self))
        logger.info(f"SAVED: {outfp}")
        
        return str(self)
        
    def change_reftime(
        self,
        newreftime: datetime.datetime,
    ):
        """
        Shift reference time of arrival picks.
        
        Parameters
        ----------
        newreftime: datetime.datetime
            A new reference time but only units greater than minute are used.
        """
        # =======================
        # CHECK
        # =======================
        if hasattr(self, "reftime") == False:
            raise AttributeError("No reftime data. self.reftime is required.")
        if hasattr(self, "arrivals") == False:
            raise AttributeError("No arrival data. self.arrivals is required.")
        if newreftime.second != 0 or newreftime.microsecond != 0:
            raise ValueError(f"newreftime should not have units smaller than minute. Now given {newreftime.second}s, {newreftime.microsecond}us ")
        # =======================
        # MAIN
        # =======================
        dt = (self.reftime - newreftime).total_seconds()
        
        if dt == 0:
            logger.debug("No change in reftime.")
            return
        
        self.reftime = newreftime
        
        for i in range(len(self.arrivals)):
            if self.arrivals.loc[i,"ptime"] != 0:
                self.arrivals.loc[i,"ptime"] += dt
            if self.arrivals.loc[i,"stime"] != 0:
                self.arrivals.loc[i,"stime"] += dt
        
        logger.debug(f"New reftime: {self.reftime.strftime('%y/%m/%d %H:%M')} ({dt:+.3f}s)")
        return
    
    # ##########################
    # HELPER
    # ##########################
    # def __make__(
    #     self,
    #     refyyyy: int,
    #     refmm: int,
    #     refdd: int,
    #     refHH: int,
    #     refMM: int,
    #     stnlat: list[float],
    #     stnlon: list[float],
    #     stnelv_m: list[float],
    #     stncode: list[str],
    #     polarity: list[str] = [],
    #     ptime: list[float] = [],
    #     pcert: list[float] = [],
    #     stime: list[float] = [],
    #     scert: list[float] = [],
    #     fptime: list[float] = [],
    #     maxamp: list[float] = [],
    #     pcorrection: list[float] = [],
    #     scorrection: list[float] = [],
    # ):
    #     self.reftime = datetime.datetime(
    #         refyyyy, refmm, refdd, refHH, refMM
    #     )
    #     self.make
        
    
    @staticmethod
    def make(
        refyy: int,
        refmm: int,
        refdd: int,
        refHH: int,
        refMM: int,
        stnlat: list[float],
        stnlon: list[float],
        stnelv_m: list[float],
        stncode: list[str],
        polarity: list[str] = [],
        ptime: list[float] = [],
        pcert: list[float] = [],
        stime: list[float] = [],
        scert: list[float] = [],
        fptime: list[float] = [],
        maxamp: list[float] = [],
        pcorrection: list[float] = [],
        scorrection: list[float] = [],
        savedir:str = ".",
        savename:str = None,
        overwrite:bool = False,
        save:bool = False,
        ):
        """
        Generate text for seis file.
        
        .. versionadded:: 0.2.0
        
        Parameters
        ----------
        refyy: int
            Year of reference time.
        refmm: int
            Month of reference time.
        refdd: int
            Date of reference time.
        refHH: int
            Hour of reference time.
        refMM: int
            Minute of reference time.
        stnlat: list
            Latitude of stations.
        stnlon: list
            Longitude of stations.
        stnelv_m: list
            Elevation of stations [m].
        stncode: list
            Station codes.
            Its length should be shorter than 10 characters.
        polarity: list[str]
            Polarity of P wave.
            "U"(Up), "D"(Down), "."(No data) are allowed.
            If not given, all polarities will be set to ".".
        ptime: list[float]
            Arrival time of P wave in seconds from the referential time(given by refyy,refmm,...,refMM).
            If there is no pick of P arrival at the certain channel, please set the value to None or np.nan.
            At that case, pcert will be automatically set to 0
            at that channel.
        stime: list[float]
            Arrival time of S wave in seconds from the referential time(given by refyy,refmm,...,refMM).
            If there is no pick of P arrival at the certain channel, please set the value to None or np.nan.
            At that case, pcert will be automatically set to 0
            at that channel.
        pcert: list[float]
            Certainty of arrival time of P wave.
            If ptime is None or np.nan, 
            this value will be automatically set to 0.
        scert: list[float]
            Certainty of arrival time of S wave.
            If stime is None or np.nan, 
            this value will be automatically set to 0.
        fptime: list[float]
            F-P time in second.
            If not given, set to 0.
        maxamp: list[float]
            Maximum amplitude.
            If not given, set to 0.
        pcorrection: list[float]
            Station correction value [s] for P wave.
            If not given, set to 0.
        scorrection: list[float]
            Station correction value [s] for S wave.
            If not given, set to 0.
        """
        # ========================================================================
        # start
        # ======================================================================
        nrow = len(stnlat)
        
        if len(polarity) == 0:
            polarity = ["."]*nrow
        
        if len(ptime) == 0:
            ptime = [0]*nrow
        if len(pcert) == 0:
            pcert = [0]*nrow
        if len(stime) == 0:
            stime = [0]*nrow
        if len(scert) == 0:
            scert = [0]*nrow
        
        if len(fptime) == 0:
            fptime = [0]*nrow
        if len(maxamp) == 0:
            maxamp = [0]*nrow
        if len(pcorrection) == 0:
            pcorrection = [0]*nrow
        if len(scorrection) == 0:
            scorrection = [0]*nrow
        
        # ----------------------
        # station correction
        # ----------------------
        pcorrection = pd.Series(pcorrection).astype(float)
        scorrection = pd.Series(scorrection).astype(float)
        pcorrection.replace(np.nan,0,inplace=True)
        scorrection.replace(np.nan,0,inplace=True)
        
        _pcorrection = pcorrection.copy().astype(str)
        _scorrection = scorrection.copy().astype(str)
        for i in range(nrow):
            if pcorrection.iloc[i] != 0:
                _pcorrection.iloc[i] = f"{pcorrection.iloc[i]:>7.3f}"
            else:
                _pcorrection.iloc[i] = " "*7
            if scorrection.iloc[i] != 0:
                _scorrection.iloc[i] = f"{scorrection.iloc[i]:>7.3f}"
            else:
                _scorrection.iloc[i] = " "*7
            
            if _pcorrection.iloc[i] == " "*7 and _scorrection.iloc[i] == " "*7:
                _pcorrection.iloc[i] = ""
                _scorrection.iloc[i] = ""
                
        # =======================
        # MAIN
        # =======================
        text = ""
        
        # 1行目
        now = datetime.datetime.now().strftime("%y/%m/%d %H:%M:%S")
        if 0 <= refyy < 10:
            strrefyy = f"{refyy:02.0f}"
        else:
            strrefyy = str(refyy)[-2:]
        text += f"{strrefyy}/{refmm:02.0f}/{refdd:02.0f} {refHH:02.0f}:{refMM:02.0f}                   {now}\n"

        # 2行目
        for i in range(nrow):
            # handle pcert, scert for not picked case -----------
            if ptime[i] is None or np.isnan(ptime[i]):
                ptime[i] = 0
                pcert[i] = 0
            if stime[i] is None or np.isnan(stime[i]):
                stime[i] = 0
                scert[i] = 0
                
            # MAIN: write -----------
            text += f"{stncode[i]:<10} {polarity[i]:1}{ptime[i]:>8.3f}{pcert[i]:>6.3f}{stime[i]:>8.3f}{scert[i]:>6.3f}{fptime[i]:>6.1f}{maxamp[i]:9.2e}{stnlat[i]:11.5f}{stnlon[i]:11.5f}{stnelv_m[i]:>7.0f}{_pcorrection.iloc[i]}{_scorrection.iloc[i]}"
            text += '\n'
        
        if save:
            if not os.path.exists(savedir):
                os.makedirs(savedir)
            
            if savename is None:
                savename = (
                    f"{refyy}{refmm}{refdd}-"
                    f"{refHH}{refMM}{np.min(ptime):04.2f}"
                    f".seis"
                    )
            
            savefp = os.path.join(savedir, savename)
            
            if os.path.exists(savefp) and not overwrite:
                logger.warning(f"SKIP: File already exists: {savefp}")
            else:
                with open(savefp,'w') as f:
                    f.write(text)
                    logger.info(f"SAVED: {savefp}")
        
        return text


# ##########################
# initial
# ##########################
def read_seis(fp:str):
    """
    Read a seis file of win and return a Seis object.
    """
    seis = Seis()
    seis.read(fp)
    return seis
# %%

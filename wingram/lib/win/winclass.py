"""
Classes to handle WIN data.

-v0.3.0-a1
    - created 2024/09/14
    - enhanced: from_obspy 2024/09/14
    - add WIN.select 2024/09/20
    - add some properties to WIN1ch and WIN 2024/09/20
    - add WIN.__setitem__, __add__, __len__, WIN1ch.__add__ 2024/09/20
    - add WIN.write 2024/09/21
    - bug fix: WIN.plot 2024/09/21
        handling of starttime and endtime

"""
from multiprocessing import Value
import os
import re
import copy
import numpy as np
import scipy
from scipy.signal import butter, filtfilt, hilbert, decimate, detrend, correlate
import pandas as pd
import matplotlib.pyplot as plt
import datetime

from bitarray import bitarray

from dataclasses import dataclass

from ...utils.log import logger
from ...utils.timehandler import yy2yyyy
from ...utils.unithandler import diff_unit, integrate_unit
from ..chtable.reader import read_chtable
from ..chtable.chtable_index import IDX as CHTABLE_IDX
from .reader.core import __readwin__
from .writer.helper import __1ch2bin__, __add_header__, __satisfy_sample_size__, __auto_sample_size__

# ##########################
# WIN data
# ##########################
def read(
    fp:str|list[str],
    chtable:str = None,
    encoding:str = "utf-8",
    apply_calib:bool = False,
    **kwargs,
    ):
    """
    Read WIN file(s).
    If there is a channel table file whose name is fp+".ch", 
    the channel table is automatically read.
    If channel table is given, it will be loaded and applied to the data.

    Parameters
    ----------
    fp : list[str]
        File path of WIN data.
    chtable : str, optional
        File path of channel table, by default None
    encoding : str, optional
        Encoding of the channel table, by default "utf-8"
    apply_calib : bool, optional
        If True, apply calibration factor to output data, by default False

    Returns
    -------
    win: WIN or WIN1ch
        WIN or WIN1ch class.
    """
    win = WIN()
    win.read(fp,**kwargs)
    if chtable is not None and isinstance(win, WIN):
        win.read_chtable(
            chtable,
            encoding=encoding,
            apply_calib=apply_calib,
            )
    elif (
        chtable is None 
        and os.path.exists(f"{fp}.ch")
        ):
        try:
            win.read_chtable(
                f"{fp}.ch",
                encoding=encoding,
                apply_calib=apply_calib,
                )
            logger.debug(f"Channel table was automatically detected: {fp}.ch")
        except:
            pass
    return win

def from_obspy(
    obspy_data,
    chtable:str = None,
    encoding:str = "utf-8",
    apply_calib:bool = False,
    ):
    """
    Generate WIN or WIN1ch class from Obspy Stream or Trace class.
    
    Parameters
    ----------
    obspy_data: obspy.Stream or obspy.Trace
        Obspy Stream or Trace class.
    
    """
    out = WIN.from_obspy(obspy_data)
    if chtable is not None:
        out.read_chtable(
            chtable,
            encoding=encoding,
            apply_calib=apply_calib,
        )
    return out

@dataclass
class Params:
    """
    Class to handle parameters of WIN data.
    
    Attributes
    ----------
    ch: str
        [1] Read only.
        Channel number of the parent WIN1ch data.
    station: str
        [4] Station code within 10 characters.
    component: str
        [5] Component code within 6 characters.
    unit: str
        [9] Unit of the data.
        
    sensitivity: float
        [8] Sensitivity of the sensor [V/self.unit].
    ad_gain: float
        [12] Gain of the AD converter.
    ad_bit_step: int
        [13] Step of the AD converter.
        
    lat: float
        [14] Latitude of the station [deg].
    lon: float
        [15] Longitude of the station [deg].
    elv: float
        [16] Elevation of the station [m].
    p_correction: float
        [17] Correction time for P wave [s].
    s_correction: float
        [18] Correction time for S wave [s].
    
    monitor_size: int
        [6] Size in which the data is shown in the monitor of WIN system.
    
    flag: int
        [2] "回収フラグ," retrieval flag. Not used in general.
    delay_time: int
        [3] Delay time results from telecommunication [ms]. Not used in general.
    ad_bit_size: int
        [7] Bit size of AD converter. Not used in general.
    natural_period: float
        [10] Natural period of the sensor. Not used in general.
    damping: float
        [11] Damping constant of the sensor. Not used in general.
    
    note: str
        [19] Comment to write in the channel table.
    
    fmin: float
        Lower limit of frequency filter.
    fmax: float
        Upper limit of frequency filter.

    calib: float
        Read only.
        Calibration factor to convert bit to physical value.
    """
    parent = None
    
    fmin:float = None
    fmax:float = None
    
    # chtable:pd.Series = None
    
    flag:int = 1 #[2]
    delay_time:int = 1 #[3]
    station:str = None #[4]
    component:str = None #[5]
    monitor_size:int = 3 #[6]
    ad_bit_size:int = 20 #[7]
    sensitivity:float = 1 #[8]
    unit:str = "." #[9]
    natural_period:float = 1 #[10]
    damping:float = 1 #[11]
    ad_gain:float = 0 #[12]
    ad_bit_step = 1 #[13]
    lat:float = 0 #[14]
    lon:float = 0 #[15]
    elv:float = 0 #[16]
    p_correction:float = 0 #[17]
    s_correction:float = 0 #[18]
    note:str = "" #[19]
    
    # calib:float = 1
    is_calibed:bool = False
    # bit_step:int = None
    
    _attributes = [
        'parent',
        'ch',
        'flag',
        'delay_time',
        'station',
        'component',
        'monitor_size',
        'ad_bit_size',
        'sensitivity',
        'unit',
        'natural_period',
        'damping',
        'ad_gain',
        'ad_bit_step',
        'lat',
        'lon',
        'elv',
        'p_correction',
        's_correction',
        'note',
    ]
    
    # =======================
    # property
    # =======================
    @property
    def ch(self):
        return self.parent.ch
    
    @property
    def calib(self):
        """
        Return calibration factor.
        1/[8]*[13]/(10^([12]/20))
        """
        return 1 /self.sensitivity *self.ad_bit_step /(10**(self.ad_gain/20))
    
    @property
    def chtable(self):
        """
        Return a list for a row of channel table.
        """
        out = [
            self.ch,
            self.flag,
            self.delay_time,
            self.station,
            self.component,
            self.monitor_size,
            self.ad_bit_size,
            self.sensitivity,
            self.unit,
            self.natural_period,
            self.damping,
            self.ad_gain,
            self.ad_bit_step,
            self.lat,
            self.lon,
            self.elv,
            self.p_correction,
            self.s_correction,
            self.note,
        ]
        return out
    
    # =======================
    # Magic Method
    # =======================
    def __init__(self, parent):
        self.parent = parent
        return
    
    def __repr__(self):
        txt = ""
        for i in range(len(vars(self))):
            txt += f"{list(vars(self).keys())[i]}\t: {list(vars(self).values())[i]}\n"
        return txt
    
    def __getitem__(self, key):
        if isinstance(key, str):
            return vars(self)[key]
        elif isinstance(key, int):
            return self._attributes[key]
        elif isinstance(key, slice):
            return [getattr(self, attr) for attr in self._attributes[key]]
        else:
            raise ValueError(f"Invalid key type: {type(key)}")

    def __setitem__(self, key, value):
        def is_property(obj, attr):
            return isinstance(getattr(type(obj), attr, None), property)
        
        if isinstance(key, str):
            if is_property(self, key):
                raise AttributeError(
                    f"Cannot modify property: {key}"
                    )
            setattr(self, key, value)
            
        elif isinstance(key, int):
            attr_name = self._attributes[key]
            if is_property(self, attr_name):
                raise AttributeError(
                    f"Cannot modify property: {attr_name}"
                )
            setattr(self, attr_name, value)
        
        elif isinstance(key, slice):
            if len(value) != len(self._attributes[key]):
                raise ValueError(f"Length of values does not match length of slice: {len(value)} != {len(self._attributes[key])}")
            
            for attr, val in zip(self._attributes[key], value):
                if is_property(self, attr):
                    raise AttributeError(
                        f"Cannot modify property: {attr}"
                        )
                setattr(self, attr, val)
        else:
            raise ValueError(f"Invalid key type: {type(key)}")
        return    
    
@dataclass
class WIN1ch:
    """
    Class to handle WIN data of 1 channel.
    It is preferable the sampling frequency is constant.
    
    Attributes
    ----------
    ch: str
        Channel name.
    data: np.ndarray
        Data of the channel.
    time: np.ndarray
        Time of the data.
        Should has same size as data.
    params: Params
        Parameters of the data.
    """
    _ch: str = None
    ch:str = _ch
    data:np.ndarray = None
    time:np.ndarray = None
    params = None
    
    # =======================
    # property
    # =======================
    @property
    def fs(self):
        """
        A function to get sampling frequency from time axis.
        If sampling frequency is not constant, it will return None.
        """
        return self.dt**-1
    
    @property
    def dt(self):
        if len(self.time) > 1:
            dt = np.diff(self.time)
            if np.max(dt) == np.min(dt):
                dt = dt[0].item().total_seconds()
            else:
                logger.warning("sampling frequency is not constant.")
                dt = np.array([_dt.item().total_seconds() for _dt in dt])
        elif len(self.time) == 1:
            dt = np.nan
        return dt
    
    @property
    def starttime(self):
        return self.time[0].astype(datetime.datetime)
    @property
    def endtime(self):
        return self.time[-1].astype(datetime.datetime)
    @property
    def timelength(self):
        return (self.endtime - self.starttime).total_seconds()
    
    @property
    def ch(self):
        return self._ch
    
    @ch.setter
    def ch(self, value):
        if isinstance(value, int):
            value = f"{value:04X}"
            
        if isinstance(value, str):
            if not re.match(r'^[0-9A-Fa-f]+$', value):
                raise ValueError(f"Channel name must be a hexadecimal number: {value}")
            if len(value) < 4:
                value = value.rjust(4, '0')
            elif len(value) > 4:
                raise ValueError(f"Channel name must be 4 characters: {value}")
            
        self._ch = value
    
    
    # =======================
    # Magic Method
    # =======================
    def __init__(
        self,
        data:np.ndarray = None,
        time:np.ndarray = None,
        starttime:datetime.datetime = None,
        fs = None,
        ch:str|int = None,
        ):
        
        self.params = Params(self)
        
        if (
            data is None
            and time is None
            and starttime is None 
            and fs is None
            ):
            return
        
        # =======================
        # check
        # =======================
        if (
            (data is not None or time is None)
            and (starttime is None and fs is None)
            ):
            raise AssertionError(
                "Either time or starttime and fs must be given."
                )
        
        if data is not None:
            self.data = data
            if time is not None:
                self.time = time
            else:
                _dt = datetime.timedelta(seconds=1/fs)
                _endtime = starttime + datetime.timedelta(seconds=len(data)/fs)
                self.time = np.arange(
                    starttime,
                    _endtime,
                    _dt,
                )
        
        if ch is not None:
            # if isinstance(ch, int):
            #     ch = f"{ch:04X}"
            self.ch = ch
            # self._ch = ch
            
        return
        
    def __repr__(self):
        st = self.starttime.strftime('%Y/%m/%dT%H:%M:%S')
        et = self.endtime.strftime('%Y/%m/%dT%H:%M:%S')
        # if isinstance(self.fs, (int,float) ):
        #     trange = self.params.timelength + self.dt
        # else:
        #     trange = self.params.timelength
        txt = ""
        txt += f"ch\t:{self.ch} ({self.params.station}-{self.params.component}) \n"
        # txt += f"data sample\t:{len(self.data)} \n"
        txt += f"time\t:{st} - {et} ({self.timelength:.1f}s) \n"
        txt += f"fs\t:{self.fs} (dt = {self.dt}s)\n"
        txt += f"unit\t:{self.params.unit} \n"
        txt += f"calib\t:{self.params.calib} (is_calibed: {self.params.is_calibed})\n"
        txt += f"filter\t:fmin = {self.params.fmin} - fmax = {self.params.fmax} Hz\n"
    
        return txt
    
    def __str__(self):
        txt = ""
        txt += f"{self.ch} ({self.params.station}-{self.params.component})\t| "
        txt += f"fs: {self.fs} Hz, "
        txt += f"unit: {self.params.unit}\t| "
        if isinstance(self.time, np.ndarray):
            # WIN.dataから呼び出した際に，timeがndarrayでなく0番目の要素（datetime）として誤処理されるpandasのバグ?への対策
            st = self.starttime.strftime('%Y/%m/%dT%H:%M:%S')
            et = self.endtime.strftime('%Y/%m/%dT%H:%M:%S')
            txt += f"{st} - {et} ({self.timelength:.1f}s)"

        return txt
    
    def __len__(self):
        return len(self.data)
        
        
    def __getitem__(
        self,
        key:int|slice|list[int]|list[str],
        ):
        if isinstance(key, (int, slice)):
            if isinstance(key, slice) and key.step is not None:
                logger.warning(
                    "Using step for downsampling is not recommended because of aliasing."
                    "Apply anti-alias filter before downsampling."
                    )
            outdata = WIN1ch()
            outdata.ch = self.ch
            outdata.params = self.params
            outdata.data = self.data[key]
            outdata.time = self.time[key]
            return outdata
        else:
            raise ValueError(f"Invalid key type: {type(key)}")
    
    def __add__(self, other):
        if isinstance(other, WIN1ch):
            if self.ch == other.ch and (self.ch is not None and other.ch is not None):
                raise ValueError(f"Channel {self.ch} is already in the data.")
            else:
                _tar = pd.Series(
                    self,
                    index = [self.ch],
                )
                _new = pd.Series(
                    other,
                    index = [other.ch],
                )
                _outdf = pd.concat([_tar, _new], axis=0)
                out = WIN()
                out.data = _outdf
                return out
        elif isinstance(other, WIN):
            return other.__add__(self)
        else:
            raise ValueError(f"Cannot add WIN1ch and {type(other)}")
    
    def __radd__(self, other):
        if isinstance(other, WIN1ch):
            return self.__add__(other)
        elif isinstance(other, WIN):
            return other.__add__(self)
        else:
            raise ValueError(f"Cannot add WIN1ch and {other} {type(other)}")
        
    # =======================
    # generate
    # =======================
    @staticmethod
    def from_obspy(tr):
        import obspy
        if not isinstance(tr, obspy.Trace):
            raise ValueError(f"Input must be Obspy Trace class, not {type(tr)}.")
        out = WIN1ch()
        out.data = tr.data
        
        st = tr.stats.starttime.datetime
        et = tr.stats.endtime.datetime
        dt = datetime.timedelta(seconds=tr.stats.delta)
        time = np.arange(
            st,
            et + dt,
            dt,
        )
        # time = time.astype(np.datetime64)
        out.time = time
        # out.get_fs()
        # if tr.stats.station == "":
        #     out.ch = tr.stats.channel
        # else:
        out.params.station = tr.stats.station
        out.params.component = tr.stats.channel
        out.params.ad_bit_step = out.params.ad_bit_step * tr.stats.calib
        return out
    
    
    # =======================
    # basic
    # =======================
    # def get_fs(self):
    #     """
    #     A function to get sampling frequency from time axis and hold it in self.fs.
    #     If sampling frequency is not constant, it will return None.
    #     """
    #     dt = np.diff(self.time)
    #     if np.max(dt) == np.min(dt):
    #         fs = dt[0].item().total_seconds() ** (-1)
    #     else:
    #         logger.warning("sampling frequency is not constant.")
    #         fs = None
    #     self.fs = fs
    #     return fs
    
    def calibrate(self):
        """
        Apply calibration factor to data.
        """
        if not self.params.is_calibed:
            self.params.is_calibed = True
            self.data = self.data * self.params.calib
        else:
            pass
        return self
    
    def decalibrate(self):
        """
        Remove calibration factor from data.
        """
        if self.params.is_calibed:
            self.params.is_calibed = False
            self.data = self.data / self.params.calib
        else:
            pass
        return self
    
    # =======================
    # Processing
    # =======================
    def shift_time(self, timedelta: datetime.timedelta):
        """
        Shift time axis.
        """
        # ----------------------
        # check
        # ----------------------
        assert isinstance(timedelta, datetime.timedelta), f"timedelta must be datetime.timedelta, not {type(timedelta)}"
        
        # ----------------------
        # main
        # ----------------------
        _dt = datetime.timedelta(seconds=self.dt)
        self.time = np.arange(
            self.starttime + timedelta,
            self.endtime + timedelta + _dt,
            _dt,
        )
        return self
    
    def demean(self):
        """
        Remove mean from data.
        """
        self.data = self.data - np.mean(self.data)
        return self
    
    def detrend(self):
        """
        Remove trend from data.
        """
        import scipy
        self.data = scipy.signal.detrend(
            self.data,
            type="linear",
            )
        return self
    
    def gradient(self):
        """
        Calculate gradient of data.
        """
        self.data = np.gradient(self.data) / self.dt
        self.params.unit = diff_unit(self.params.unit)
        return self
    
    def cumsum(self):
        """
        Calculate integration of data.
        """
        self.data = np.cumsum(self.data)
        self.params.unit = integrate_unit(self.params.unit)
        return self
    
    def integrate(self):
        """
        Calculate integration of data using scipy.
        """
        # 台形積分
        self.data = scipy.integrate.cumulative_trapezoid(
            y = self.data,
            dx = self.dt,
            initial = 0,
            )
        self.params.unit = integrate_unit(self.params.unit)
        return self
    
    def bandpass(
        self,
        fmin: float=None, 
        fmax: float=None,
        filt_order:int = 3,
        ):
        """
        チャンネルごとにバンドパスフィルターをかける．
        """
        from ...utils.process.filter import bandpass
        
        self.data = bandpass(
            data = self.data,
            fs = self.fs,
            fmin = fmin,
            fmax = fmax,
            filt_order = filt_order,
            )
        
        self.params.fmin = fmin
        self.params.fmax = fmax
        return self
    
    def taper(
        self,
        taper_ratio:float,
    ):
        """
        Apply taper to data.
        """
        from ...utils.process.taper import taper
        
        self.data = taper(
            data = self.data,
            taper_points = int(len(self.data)*taper_ratio),
            )
        return self
    
    def decimate(
        self,
        new_fs:int,
    ):
        """
        Downsample data.
        """
        q = int(self.fs/new_fs)
        self.data = decimate(
            self.data,
            q,
            zero_phase=True,
            )
        self.time = self.time[::q]
        
        self.params.fmax = new_fs/2
        return self
    
    def trim(
        self,
        starttime:datetime.datetime = None,
        endtime:datetime.datetime = None,
        contain_end:bool = True,
        ):
        """
        Trim data based on time.
        """
        # ----------------------
        # check
        # ----------------------
        if starttime is None and endtime is None:
            raise ValueError("Either starttime or endtime must be given.")
        if starttime is not None and endtime is not None:
            if starttime >= endtime:
                raise ValueError(f"Start time is same or later than end time. starttime: {starttime}; endtime: {endtime}")
        if starttime is not None:
            if starttime > self.endtime:
                raise ValueError(f"Start time is later than the end time of the data. {starttime} > {self.endtime}")
        if endtime is not None:
            if endtime < self.starttime:
                raise ValueError(f"End time is earlier than the start time of the data. start")
        
        # ----------------------
        # find index
        # ----------------------
        if starttime is not None:
            idx_start = np.where(self.time >= starttime)[0][0]
        else:
            idx_start = 0
            
        if endtime is not None:
            if contain_end:
                idx_end = np.where(self.time <= endtime)[0][-1]
            else:
                idx_end = np.where(self.time < endtime)[0][-1]
        else:
            idx_end = len(self.time)-1
        
        # ----------------------
        # trim
        # ----------------------
        outdata = self[idx_start:idx_end+1]
        return outdata
    
    def copy(self):
        """
        Return a copy of the data.
        """
        out = copy.deepcopy(self)
        return out
    
    # =======================
    # Converter
    # =======================
    def to_obspy(self):
        """
        Convert to Obspy Trace class.
        """
        import obspy
        tr = obspy.Trace(self.data)
        tr.stats.sampling_rate = self.fs
        tr.stats.starttime = obspy.UTCDateTime(self.starttime)
        
        if self.params.station is not None and self.params.component is not None:
            tr.stats.station = self.params.station
            tr.stats.channel = self.params.component
            tr.stats.chnumber = self.ch
        else:
            tr.stats.channel = self.ch
            tr.stats.chnumber = self.ch
        tr.stats.calib = self.params.calib
        tr.stats._format = "WIN"
        return tr
    
    def to_int(self):
        out = self.copy()
        
        float_data = out.data
        # 最大4Byteのデータの3Byteに収まるよう拡縮．
        std  = np.std(float_data)
        _tmp_max = np.max(abs(float_data))/std
        if _tmp_max > 2**32:
            scale_factor = np.max(abs(float_data)) / (2**31/2)
        else:
            scale_factor = std / (2**8/2)
        int_data = (float_data / scale_factor).astype(int)
        
        out.params.ad_bit_step = out.params.ad_bit_step * scale_factor
        out.data = int_data
        return out
    
    def __to_bit__(
        self,
        sample_size:int = None,
        boundary = "cut",
        force_make_int:bool = False,
        ) -> tuple[list[datetime.datetime],list[bitarray]]:
        data = self.copy()
        # =======================
        # check
        # =======================
        if data.ch is None:
            raise ValueError("Channel number is not given.")
        
        if data.params.is_calibed:
            data.decalibrate()
        
        if not np.issubdtype(data.data.dtype, np.integer):
            data = data.to_int()
            # logger.info("Data is converted to integer.")
        
        # ----------------------
        # auto sample size
        # ----------------------
        # if sample_size is None:
        #     # 全ての秒セクションで同じサンプルサイズにするよう試行する
        #     if __satisfy_sample_size__(data.data,5,signed=True):
        #         sample_size = __auto_sample_size__(data.data)
        #         logger.debug(f"auto sample_size: {sample_size}")
        #     else:
        #         # ムリであれば各秒セクションごとに異なるサンプルサイズを試みる．
        #         # __1ch2bin__内で自動処理されるのでそこに任せる．
        #         pass
        
        # =======================
        # split into 1s sections
        # =======================
        st = data.starttime
        et = data.endtime
        if boundary == "cut":
            if st.microsecond == 0:
                winst = st
            else:
                winst = st + datetime.timedelta(microseconds=1000000-st.microsecond)
                logger.warning(f"{self.ch}: Cutting the first {st.microsecond/1e6} s.")
            if et.microsecond == (1-data.dt)*10**6:
                winet = et
            else:
                winet = et - datetime.timedelta(microseconds=et.microsecond)
                logger.warning(f"{self.ch}: Cutting the last {et.microsecond/1e6} s.")
                
            data.trim(
                starttime = winst,
                endtime = winet,
                contain_end=True,
            )
        elif boundary == "padding" or 'zero-padding':
            if st.microsecond == 0:
                winst = st
            else:
                winst = st - datetime.timedelta(microseconds=st.microsecond)
            if et.microsecond == (1-data.dt)*10**6:
                winet = et
            else:
                winet = et + datetime.timedelta(microseconds=1000000-et.microsecond)
            
            # padding data -----------
            st_pad_data = (np.ones(
                int((st - winst).total_seconds() * data.fs),
            )*data.data[0]).astype(int)
            et_pad_data = (np.ones(
                int((winet - et).total_seconds() * data.fs),
            )*data.data[-1]).astype(int)
            
            if boundary == "zero-padding":
                et_pad_data *= 0
                et_pad_data *= 0
            
            newdata = np.concatenate([st_pad_data, data.data, et_pad_data])
            
            newtime = np.arange(
                winst,
                winet + datetime.timedelta(seconds=data.dt),
                datetime.timedelta(seconds=data.dt),
            )
            if len(newdata) != len(newtime):
                raise ValueError(f"Length of padded data ({len(newdata)}) and time ({len(newtime)}) is different.")
            data.data = newdata
            data.time = newtime

        n_section = int(np.ceil((winet - winst).total_seconds()))
        
        stlist = [None]*n_section
        outlist = [None]*n_section
        for i in range(n_section):
            _temp1s = data.trim(
                starttime = winst + datetime.timedelta(seconds=i),
                endtime = winst + datetime.timedelta(seconds=i+1),
                contain_end = False,
                )
            stlist[i] = _temp1s.starttime
            outlist[i] = __1ch2bin__(
                data = _temp1s.data,
                fs = _temp1s.fs,
                chnumber = int(_temp1s.ch,16),
                sample_size = sample_size,
                force_make_int = force_make_int,
            )
        outsr = pd.Series(outlist, index = stlist)
        return outsr
    
    def write(self, fp:str,**kwargs)->None:
        """
        Write WIN file.
        """
        bitdf = self.__to_bit__(**kwargs)
        out = bitarray()
        # return bitdf
        for i in range(len(bitdf)):
            _tmp = __add_header__(
                    bitdf.iloc[i],
                    starttime = bitdf.index[i],
                )
            out.extend(_tmp)
        with open(fp, "wb") as f:
            f.write(out)
            logger.info(f"Saved: {fp}")
        return
    
    # =======================
    # Viewer
    # =======================
    def plot(
        self,
        title:str = "",
        lw = 0.5,
        c = "k",
        **kwargs,
        ):
        from .viewer.plot_wave import __wave__
        
        # title -----------
        if title == "":
            if self.ch is not None:
                title += f"ch: {self.ch} "
            if self.params.station is not None:
                title += "["
                title += f"{self.params.station}"
                if self.params.component is not None:
                    title += f"-{self.params.component}"
                title += "] "
            elif self.params.component is not None:
                    title += f"[cmp: {self.params.component}]"

            title += " | "
            title += (
                f"{self.starttime.strftime('%Y/%m/%d %H:%M:%S')}-"
                f"{self.endtime.strftime('%Y/%m/%d %H:%M:%S')}"
            )
        
        # ylabel -----------
        if self.params.unit is not None and self.params.is_calibed:
            ylabel = f"[{self.params.unit}]"
        else:
            ylabel = "Amplitude"
        
        fig, ax = __wave__(
            self.data,
            self.time,
            title = title,
            ylabel = ylabel,
            lw = lw,
            c = c,
            **kwargs,
        )
        return fig, ax
    

@dataclass
class WIN:
    """
    Class to hold multiple WIN data.
    It is preferable that each sampling frequency is constant.
    
    Parameters
    ----------
    data: pd.DataFrame
        It holds channel number as index and WIN1ch class as data.
    chtable: pd.DataFrame
        Loaded channel table.
        Use read_chtable(fp) to load channel table.
    """
    fp:list[str] = None
    chtablefp:str = None
    data = None
    
    @property
    def ch(self):
        out = [None]*len(self.data)
        for i in range(len(self.data)):
            out[i] = self.data.iloc[i].ch
        return out
    
    @property
    def chtable(self):
        value_out = []
        for i in range(len(self.data)):
            value_out.append(self.data.iloc[i].params.chtable)
        return pd.DataFrame(value_out, columns = CHTABLE_IDX)
            
    
    def __repr__(self):
        txt = ""
        txt += f"fp: {self.fp}, chtablefp: {self.chtablefp}\n"
        txt += "data:\n"
        for i in range(len(self.data)):
            txt += f"{i:>5g}: {str(self.data.iloc[i])}\n"
        # txt += f"chtable: {str(self.chtable)}"
        return txt
    
    def __getitem__(self, key):
        if isinstance(key, int):
            # return WIN1ch object -----------
            outdata = self.data.iloc[key]
            return outdata
        elif isinstance(key, slice):
            outdata = copy.deepcopy(self)
            outdata.data = self.data.iloc[key]
            
        elif isinstance(key, str):
            # return WIN1ch object -----------
            outdata = self.data.loc[key]
            return outdata
        elif isinstance(key, list):
            # check type -----------
            if all(isinstance(item, str) for item in key):
                outdata = copy.deepcopy(self)
                outdata.data = self.data.loc[key]
                return outdata
            elif all(isinstance(item, int) for item in key):
                outdata = copy.deepcopy(self)
                outdata.data = self.data.iloc[key]
                return outdata
            else:
                raise ValueError("Items in the key must be all str or all int when it is given by list.")
        
        return outdata

    def __setitem__(self, key, value):
        if isinstance(value, WIN1ch):
            self.data.loc[key] = value
        else:
            raise ValueError("Value must be WIN1ch class.")
    
    def __len__(self):
        return len(self.data.index)
        
    def __add__(self, other):
        if isinstance(other, WIN1ch):
            # ----------------------
            # check dupulicated channel
            # ----------------------
            if other.ch is not None and other.ch in self.data.index:
                raise ValueError(f"Channel {other.ch} is already in the data.")
            # ----------------------
            # add WIN1ch
            # ----------------------
            out = copy.deepcopy(self)
            _new = pd.Series(
                other,
                index = [other.ch],
            )
            out.data = pd.concat([self.data, _new], axis=0)
        elif isinstance(other, WIN):
            # ----------------------
            # add WIN1ch
            # ----------------------
            out = copy.deepcopy(self)
            if self.fp is None:
                out.fp = other.fp
            elif other.fp is None:
                out.fp = self.fp
            else:
                out.fp = self.fp.append(other.fp)
                
            if self.chtablefp is None:
                out.chtablefp = other.chtablefp
            elif other.chtablefp is None:
                out.chtablefp = self.chtablefp
            else:
                out.chtablefp = self.chtablefp.append(other.chtablefp)
            out.data = pd.concat([self.data, other.data], axis=0)
        else:
            raise ValueError(f"Cannot add WIN and {type(other)}")
        return out
    
    def __radd__(self, other):
        if isinstance(other, WIN1ch):
            return self.__add__(other)
        
    # =======================
    # read
    # =======================
    def read(
        self,
        fp:list[str],
        sort:bool = True,
        ch:list[str] = None,
        targettime:datetime.datetime = None,
        beforesec:int = None,
        aftersec:int = None,
        starttime:datetime.datetime = None,
        endtime:datetime.datetime = None,
        filenameformat:str = None,
        ):
        """
        Read WIN files.
        Time range can be specified by either of 
        set of (targettime, beforesec, aftersec),
        of set of (starttime, and endtime).
        If the both set are given, the latter will be used.
        
        Parameters
        ----------
        fp: list[str]
            File path of WIN data.
        sort: bool, optional, default True
            If True, sort the returned data by channel number.
        ch: list[str], optional
            List of channel number to exclusively read.
        targettime: datetime.datetime, optional
            Target time to read data. Used with beforesec and aftersec.
        beforesec: int, optional
            Time before the target time to read.
        aftersec: int, optional
            Time after the target time to read.
        starttime: datetime.datetime, optional
            Start time to read data. Used with endtime.
        endtime: datetime.datetime, optional
            End time to read data. Used with starttime.
        filenameformat: str, optional
            Format of the file name.
        """
        # ----------------------
        # check
        # ----------------------
        if isinstance(fp, str):
            fp = [fp]
        
        if starttime is not None and endtime is not None:
            if any([
                targettime is not None,
                beforesec is not None,
                aftersec is not None,
                ]):
                logger.warning("Both set of (targettime, beforesec, aftersec) and (starttime, and endtime) are given. The latter will be used.")
            targettime = starttime
            beforesec = 0
            aftersec = (endtime - starttime).total_seconds()
                 
        # ----------------------
        # read
        # ----------------------
        data = __readwin__(
            fp,
            chnumber = ch,
            targettime = targettime,
            beforesec = beforesec,
            aftersec = aftersec,
            filenameformat = filenameformat,
        )
        
        # ----------------------
        # Convert to WIN1ch class
        # ----------------------
        for i in range(len(data)):
            tmp = WIN1ch()
            tmp.params = Params(tmp)
            tar = data.iloc[i]
            tmp.data = tar[0].astype(int)
            tmp.time = tar[1].astype(np.datetime64)
            tmp.ch = data.index[i]
            # tmp.get_fs()
            
            data.iloc[i] = tmp
        
        if sort:
           data.sort_index(inplace=True)
        self.data = data
        self.fp = fp
        return data
        
    def read_chtable(
        self,
        fp:str,
        encoding:str="utf-8",
        apply_calib:bool = False,
        ):
        """
        Read channel table file.
        """
        self.chtablefp = fp
        # self.chtable = read_chtable(fp,encoding=encoding)
        # self.conbine_chtable_data(apply_calib=apply_calib)
        
        chtable = read_chtable(fp,encoding=encoding)
        
        # return self
        for i in range(len(self.data)):
            ch = self[i].ch
            if ch in chtable.ch.values or ch.lower() in chtable.ch.values:
                src = chtable[chtable.ch == ch].iloc[0]
                if len(src) == 18:
                    src = pd.concat([src, pd.Series("", index=["note"])])
                    
                # do not overwrite [0]parent and [1]ch of params
                self.data.iloc[i].params[2:] = list(src)[1:]
        
        return
    
    @staticmethod
    def from_obspy(st):
        """
        Convert Obspy Stream class to WIN class.
        """
        import obspy
        if isinstance(st, obspy.Trace):
            out = WIN1ch.from_obspy(st)
        elif not isinstance(st, obspy.Stream):
            raise ValueError(f"Input must be Obspy Stream class or Trace class, not {type(st)}.")
        out = WIN()
        datalist = [None]*len(st)
        for i in range(len(st)):
            tr = st[i]
            _tmp1ch = WIN1ch.from_obspy(tr)
            datalist[i] = pd.Series(
                _tmp1ch,
                index = [_tmp1ch.ch],
            )
        out.data = pd.concat(datalist, axis=0)
        return out
    # =======================
    # basic
    # =======================
    def calibrate(self):
        """
        Apply calibration factor to data.
        """
        for i in range(len(self.data)):
            self.data.iloc[i].calibrate()
        return self
    
    def decalibrate(self):
        """
        Remove calibration factor from data.
        """
        for i in range(len(self.data)):
            self.data.iloc[i].decalibrate()
        return self
    
    def select(
            self,
            station: str = None,
            component: str = None,
        ):
        """
        Select data based on station and component.
        Supports wildcards using regular expressions.
        """
        outdata = copy.deepcopy(self)
        if station is not None:
            # ワイルドカード '*' を正規表現 '.*' に変換
            pattern_str = station.replace('*', '.*').replace('?', '.')
            # 完全一致のために '^' と '$' を追加
            pattern = re.compile(f"^{pattern_str}$")
            outdata.data = outdata.data[outdata.data.apply(lambda ch: bool(pattern.search(ch.params.station)))]
            
        if component is not None:
            # ワイルドカード '*' を正規表現 '.*' に変換
            pattern_str = component.replace('*', '.*').replace('?', '.')
            # 完全一致のために '^' と '$' を追加
            pattern = re.compile(f"^{pattern_str}$")
            outdata.data = outdata.data[outdata.data.apply(lambda ch: bool(pattern.search(ch.params.component)))]
        
        if len(outdata) == 0:
            logger.warning("No channel was found.")
        return outdata
    
    def autofill_ch(self):
        """
        Automatically fill channel number for channels where ch is None.
        Automatical ch is start with 0000 and increment by 1.
        """
        _n = 0
        
        for i in range(len(self.data)):
            if self.data.iloc[i].ch is not None:
                continue
            _auto_ch = f"{_n:04X}"
            while _auto_ch in self.data.index:
                _n += 1
                _auto_ch = f"{_n:04X}"
            self.data.iloc[i].ch = f"{i:04X}"
            _n += 1
        return self
    
    # =======================
    # Processing
    # =======================
    def shift_time(self):
        """
        Shift time axis.
        """
        for i in range(len(self.data)):
            self.data.iloc[i] = self.data.iloc[i].shift_time()
        return self
    
    def trim(
        self,
        starttime:datetime.datetime = None,
        endtime:datetime.datetime = None,
        ):
        """
        Trim data based on time.
        """
        outdata = copy.deepcopy(self)
        for i in range(len(outdata.data)):
            outdata.data.iloc[i] = outdata.data.iloc[i].trim(starttime=starttime, endtime=endtime)
        return outdata
    
    def demean(self):
        """
        Remove mean from data.
        """
        for i in range(len(self.data)):
            self.data.iloc[i] = self.data.iloc[i].demean()
        return self
    
    def detrend(self):
        """
        Remove trend from data.
        """
        for i in range(len(self.data)):
            self.data.iloc[i] = self.data.iloc[i].detrend()
        return self
    
    def gradient(self):
        """
        Calculate gradient of data.
        """
        for i in range(len(self.data)):
            self.data.iloc[i].gradient()
        return self
    
    def integrate(self):
        """
        Calculate integration of data.
        """
        for i in range(len(self.data)):
            self.data.iloc[i] = self.data.iloc[i].integrate()
        return self
    
    def bandpass(
        self,
        fmin: float=None,
        fmax: float=None,
        filt_order:int = 3,
        ):
        """
        Apply bandpass filter to data.
        """
        for i in range(len(self.data)):
            self.data.iloc[i] = self.data.iloc[i].bandpass(fmin=fmin, fmax=fmax, filt_order=filt_order)
        return self
    
    def taper(self, taper_ratio:float):
        for i in range(len(self.data)):
            self.data.iloc[i] = self.data.iloc[i].taper(taper_ratio)
        return self
    
    def decimate(self, new_fs:int):
        for i, data in enumerate(self.data):
            self.data.iloc[i] = data.decimate(new_fs)
        return self
    
    def copy(self):
        """
        Return a copy of the data.
        """
        out = copy.deepcopy(self)
        for i in range(len(out)):
            out.data.iloc[i] = out.data.iloc[i].copy()
        return out
    
    # =======================
    # Converter
    # =======================
    def to_obspy(self):
        """
        Convert to Obspy Stream class.
        """
        import obspy
        st = obspy.Stream()
        for i in range(len(self.data)):
            tr = self.data.iloc[i].to_obspy()
            st.append(tr)
        return st
    
    def __to_bit__(
        self,
        sample_size:int = None,
        boundary:str = "cut",
        **kwargs,
        )->bitarray:
        """
        Convert to WIN binary format.
        Return DataFrame of bitarray for each 1s vs ch.
        """
        # =======================
        # check
        # =======================
        if sample_size is not None:
            if isinstance(sample_size, int):
                sample_size = [sample_size]*len(self)
            elif isinstance(sample_size, list):
                if len(sample_size) != len(self):
                    raise ValueError("Length of sample_size must be same as the number of channels.")
        else:
            sample_size = [None]*len(self)
        
        # =======================
        # split data into 1s
        # =======================
        bitsr = [None]*len(self)
        for i in range(len(self)):
            bitsr[i] = self.data.iloc[i].__to_bit__(
                sample_size = sample_size[i],
                boundary = boundary,
                **kwargs,
            )
        bitdf = pd.concat(bitsr, axis=1)
        bitdf.sort_index(axis=0, inplace=True)
        bitdf.columns = self.data.index
        return bitdf
    
    def write(
        self,
        savename:str = None,
        savedir:str = None,
        sample_size:int = None,
        boundary:str = "cut",
        **kwargs,
        )->None:
        """
        Write WIN file.
        
        Parameters
        ----------
        savename: str, optional
            File name to save.
        savedir: str, optional
            Directory to save.
        sample_size: int, optional
            Sample size in WIN format.
            Encouraged to be None because optimal size will be automatically estimated.
        boundary: str, optional
            Boundary condition for the data.
            "cut" or "padding" or "zero-padding"
        """
        
        bitdf = self.__to_bit__(
            sample_size = sample_size,
            boundary = boundary,
            **kwargs,
        )
        
        # concat ch bitarrays sharing time -----------
        bit1s = [None]*len(bitdf)
        for t in range(len(bitdf)):
            _tmpba = bitarray()
            for c in range(len(bitdf.iloc[t])):
                _tmpba.extend(bitdf.iloc[t,c])
            bit1s[t] = __add_header__(
                _tmpba,
                bitdf.index[t],
            )
            
        out = bitarray()
        for i in range(len(bit1s)):
            out.extend(bit1s[i])
        
        # ----------------------
        # write
        # ----------------------
        if savename is None:
            savename = f"{bitdf.index[0].strftime('%Y%m%d.%H%M%S.win')}"
        if os.path.isdir(savename):
            savedir = savename
            if not os.path.exists(savedir):
                os.makedirs(savedir)
            savename = f"{bitdf.index[0].strftime('%Y%m%d.%H%M%S.win')}"
            savename = os.path.join(savedir, savename)
        if savedir is not None:
            if not os.path.exists(savedir):
                os.makedirs(savedir)
            savename = os.path.join(savedir, savename)
        with open(savename, "wb") as f:
            f.write(out)
            logger.info(f"Saved: {savename}")
        return
    
    # =======================
    # Viewer
    # =======================
    def plot(
        self,
        title:str = "", 
        lw = 0.5,
        c = "k",
        **kwargs,
        ):
        from .viewer.plot_wave import __waves__
        
        if len(self) == 1:
            return self[0].plot(
                title = title,
                lw = lw,
                c = c,
                **kwargs,
            )
            
            
        chlabel = [None]*len(self.data)
        for i in range(len(self.data)):
            # ----------------------
            # channel number
            # ----------------------
            chlabel[i] = f"{self.data.index[i]}\n"
            
            # ----------------------
            # station and component
            # ----------------------
            if self.data.iloc[i].params.station is not None:
                chlabel[i] += f"{self.data.iloc[i].params.station}"
                if self.data.iloc[i].params.component is not None:
                    chlabel[i] += f"-{self.data.iloc[i].params.component}\n"
            elif self.data.iloc[i].params.component is not None:
                    chlabel[i] += f"cmp: {self.data.iloc[i].params.component}\n"
            
            # ----------------------
            # unit (If Applied)
            # ----------------------
            if self.data.iloc[i].params.is_calibed == True:
                chlabel[i] += f" [{self.data.iloc[i].params.unit}]"
        
        if title == "":
            st = min([self[i].starttime for i in range(len(self))]).strftime('%Y/%m/%d %H:%M:%S')
            et = max([self[i].endtime for i in range(len(self))]).strftime('%Y/%m/%d %H:%M:%S')
            title = f"{st} - {et}"
        fig, ax = __waves__(
            [self[i].data for i in range(len(self.data))],
            [self[i].time for i in range(len(self.data))],
            title = title,
            lw = lw,
            c = c,
            chlabel = chlabel,
            **kwargs,
        )
        return fig, ax
        
import os
import numpy as np
import pandas as pd
import datetime
from io import StringIO
# from ...utils.logger import logger
from ..utils import *
from ..lib import *

# ################################
# PhaseNet-DAS2win
# ################################
def pnd2seis(
    chnumber:np.array,
    chlat:np.array,
    chlon:np.array,
    chelev:np.array,
    chcode:list[str],
    pickfp:str,
    pickdf:pd.DataFrame = None,
    p_certainty = 0.015,
    s_certainty = 0.015,
    ch_in_original = True,
    ch_start:int = 0,
    ch_step:int = 1,
    fpformat4reftime:str = "",
    savedir:str = ".",
    save:bool = True,
    saveinitdir:str = ".",
    saveinit:bool = False,
    initdep:float = None,
    ):
    """
    Generate seis file from the output of PhaseNet-DAS and channel table.
    
    Parameters
    ----------
    chnumber/lat/lon/elev/code:
        The specific number/lat/lon/elev/code of each channel.
        All of them should be same size.
        The picked arrivals will be converted into seis file if the
        channel is contained by the "chnumber" list.
        That is, even if a arrival is picked by PhaseNet-DAS,
        that pick will not be written in output seis file 
        if the corresponding channel is not found in the "chnumber."
        
        
        Be used to obtain locations of each channel from chnumber in pick csv file.
    
    pickfp:
        File path to pick CSV file by PhaseNet-DAS.
    
    pickdf:
        If not None, use this DataFrame instead of reading pickfp.
        
    ch_in_original:
        if True, ch numbers in pick file converted into original ch number
        and refer to 'chnumber' argument to obtain station location.
    
    ch_start ch_step:
        required only ch_in_original is True.
        convert ch numbers in pick file to [ch_start + ChnumberInCSV * ch_step]
    
    fpformat4reftime:
        If not "", use referential time from *basename of pickfp*.
        However, only units greater than minute (%y or %Y,%m,%d,%H,%M) are used.
        ex.)
            Consider pickfp is "/**/20000102_030405.csv".
            Then if you want to define reftime as datetime.datetime(2000,1,2,3,4,5),
            you should give fpformat4reftime like: 
                fpformat4reftime = "%Y%m%d_%H%M*"
    
    Example
    -------
    If you have a channel table, chnumber/lat/lon/elev/code can be easily obtained.
    
    import wintools
    import glob

    tbl = wintools.read_chtbl("win/chtable/kamaishi.tbl")
    pick = "/pick/R_100Hz_230721-144015_59s.csv",

    pick = tarpick[i]
    wintools.pnd2seis(
        chnumber = tbl.index+200,
        chlat = tbl.lat.values,
        chlon = tbl.lon.values,
        chelev = tbl.elev.values,
        chcode = tbl.code.values,
        pickfp = pick,
        ch_in_original = True,
        ch_start = 0,
        ch_step = 2,
        savedir = "/home/anax/Projects/DAS/out/kamaishi/win/seis",
        save = True,
    )
    """
    # TODO pickのチャンネルインデックスを何とかして実際のDASチャンネルと対応させる（latlonを定めるため）．
    
    
    # =======================
    # Arrival Times
    # =======================
    """
    Index of Pick:
        channel_index,phase_index,phase_time,phase_score,phase_type
    Use:
        channel_index,phase_time,phase_type
    Not Use:
        phase_index,phase_score
    """
    # ======================
    # READ and PROCESSING
    # ======================
    if pickfp is None and pickdf is None:
        raise ValueError("Either of pickfp or pickdf should be given.")
    elif pickdf is None:
    # Check size and read CSV --------------------------
        logger.info(f"PROCESSING: {pickfp}")
        _size = os.path.getsize(pickfp)
        if _size == 0:
            logger.warning(f"EMPTY PICK FILE!: {pickfp}")
            if save:
                seis = ""
                if not os.path.exists(savedir):
                    os.makedirs(savedir)
                fname = os.path.basename(pickfp).replace(".csv",".seis")
                savefp = os.path.join(savedir, fname)
                logger.info(f"WRITING (empty): {savefp}")
                with open(savefp, 'w') as f:
                    f.write(seis)
            
            return
        else:
            pick = pd.read_csv(pickfp)
    elif pickdf is not None and pickfp is not None:
        logger.warning("Both pickfp and pickdf are given. Use pickdf.")
        pick = pickdf
    else:
        logger.info("Processing pickdf")
        # only pickdf is given
        pick = pickdf
        pass
    
    if pick.size == 0:
        logger.warning(f"SKIP! pick.size==0: {pick}")
        if save:
            seis = ""
            if not os.path.exists(savedir):
                os.makedirs(savedir)
            fname = os.path.basename(pickfp).replace(".csv",".seis")
            savefp = os.path.join(savedir, fname)
            logger.info(f"WRITING (empty): {savefp}")
            with open(savefp, 'w') as f:
                f.write(seis)

        return
    # convert type of arrival time into datetime ----------------------
    pick.phase_time = pd.to_datetime(pick.phase_time)
    
    # convert chnumber in csv pick file to original DAS ch number ----------------------
    if ch_in_original:
        pick.channel_index = ch_start + pick.channel_index * ch_step
        
    # -------------------
    # separate p and s ----------------------
    # -------------------
    p_pick = pick[pick.phase_type=='P']
    s_pick = pick[pick.phase_type=='S']
    
    # ======================
    # Extract Args for mkseis
    # ======================
    # ----------------------
    # referential time
    # ----------------------
    # referential time = min of arrival times ----------------------
    if fpformat4reftime == "":
        reftime = pick.phase_time.min()
    else:
        reftime = datetime.strptime(
            os.path.basename(pickfp),
            fpformat4reftime
            )
    
    refyy = reftime.year
    refmm = reftime.month
    refdd = reftime.day
    refHH = reftime.hour
    refMM = reftime.minute
    
    # make sure reftime does not have units smaller than minute -----------
    reftime = datetime.datetime(refyy,refmm,refdd,refHH,refMM)

    # ----------------------
    # locations, codes, relative times
    # ----------------------
    # ......................
    # prepare relative time
    # ......................
    # relative p and s times -------------------------
    p_refsec = (p_pick.phase_time - reftime).apply(lambda x:x.total_seconds()).values
    s_refsec = (s_pick.phase_time - reftime).apply(lambda x:x.total_seconds()).values
    # print(p_refsec)
    
    # ------------------------
    # Obtain locations and name 
    # ------------------------
    # ......................
    # args
    # ......................
    stnlat = []
    stnlon = []
    stnelv_m = []
    stncode = []
    ptime = []
    stime = []
    pcert = []
    scert = []
    
    unich = np.unique(pick.channel_index)
    # print(unich)
    for tarch in unich:
        # locations and codes ----------------------
        # print(tarch)
        idx = np.where(chnumber==tarch)[0]
        if len(idx) == 0:
            continue
        elif len(idx) == 1:
            idx = idx[0]
        else:
            raise ValueError(f"There is dupulicated ch number!: {tarch}")
            
        # print(tarch, idx)
        stnlat.append(chlat[idx])
        stnlon.append(chlon[idx])
        stnelv_m.append(chelev[idx])
        stncode.append(chcode[idx])
        
        # relative times ----------------------
        _pt = p_refsec[p_pick.channel_index==tarch]
        _st = s_refsec[s_pick.channel_index==tarch]
        if len(_pt)==0:
            ptime.append(0)
            pcert.append(0)
            
        else:
            ptime.append(_pt[0])
            pcert.append(p_certainty)
            
        if len(_st)==0:
            stime.append(0)
            scert.append(0)
        else:
            stime.append(_st[0])
            scert.append(s_certainty)
        
    # *DEBUG
    # nrow = len(stnlat)
    # print(stncode)
    # print(stnlat)
    # print(stnlon)
    # print(stnelv_m)
    # print(stncode)
    # print(ptime)
    # print(pcert)
    # print(stime)
    # print(scert)
    # for i in range(nrow):
    #     # print(stncode[i])
    #     # print(stnlat[i])
    #     print(f"{unich[i]:<5}]{stncode[i]:<10} {ptime[i]:>8.3f}{pcert[i]:>6.3f}{stime[i]:>8.3f}{scert[i]:>6.3f}{stnlat[i]:11.5f}{stnlon[i]:11.5f}{stnelv_m[i]:>7.0f}")
    
    # *DEBUG
    
    # =======================
    # mkseis
    # =======================
    seis = Seis.make(
        refyy = refyy,
        refmm = refmm,
        refdd = refdd,
        refHH = refHH,
        refMM = refMM,
        stnlat = stnlat,
        stnlon = stnlon,
        stnelv_m = stnelv_m,
        stncode = stncode,
        # polarity = None,
        ptime = ptime,
        pcert = pcert,
        stime = stime,
        scert = scert,
        # fptime = None,
        # maxamp = None,
        # stncorr = None,
        # savefp = None,
        save = False,
        )
    
    if save:
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        fname = os.path.basename(pickfp).replace(".csv",".seis")
        savefp = os.path.join(savedir, fname)
        logger.info(f"WRITING: {savefp}")
        with open(savefp, 'w') as f:
            f.write(seis)
    
    if saveinit:
        non0pt = np.where(np.array(ptime)<=0.,np.inf,np.array(ptime))
        # logger.info(f"non0ptime:\n{non0pt}")
        # logger.info(np.min(non0pt))
        initlat = np.array(stnlat)[non0pt==np.min(non0pt)][0]
        initlon = np.array(stnlon)[non0pt==np.min(non0pt)][0]
        if initdep is None:
            initdep = np.array(stnelv_m)[non0pt==np.min(non0pt)][0]*(-0.001) # m->km
        
        init = mkinit(
            initlat = initlat,
            initlon = initlon,
            initdep = initdep,
            # unclat = 0,
            # unclon = 0,
            # uncdep = 0,
            calc_tt = False,
        )
        if not os.path.exists(saveinitdir):
            os.mkdir(saveinitdir)
        initfname = os.path.basename(pickfp).replace(".csv",".init")
        saveinitfp = os.path.join(saveinitdir, initfname)
        logger.info(f"WRITING: {saveinitfp}")
        with open(saveinitfp, 'w') as f:
            f.write(init)
    return seis

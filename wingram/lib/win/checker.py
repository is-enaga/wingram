"""
Classes to check WIN binary data.

-v0.3.0-a1
    - created 2024/09/20
"""

from ...utils.log import logger
from .reader.parser import bit_parser

def __check_winfile__(fp):
    """
    Check header of WIN file.
    """
    segments = bit_parser.__split1s__(fp)
    
    outinfo = [None]*len(segments)
    for sec in range(len(segments)):
        logger.info(f"{sec+1}/{len(segments)}[s]")
        secinfo = {
            "bytesize": None,
            "starttime": None,
            "ch": None,
        }
        secinfo["bytesize"], secinfo["starttime"] = bit_parser.__read_1s_header__(segments[0])
        
        chsegments = bit_parser.__1s_to_ch__(segments[sec])
        secinfo["ch"] = [None]*len(chsegments)
        
        for ch in range(len(chsegments)):
            logger.info(f"\t{ch+1}/{len(chsegments)}[ch]")
            secinfo["ch"][ch] = {
                "chnum": None,
                "sample_size": None,
                "fs":None,
                "n_ch":None
            }
            try:
                (secinfo["ch"][ch]["chnum"],
                secinfo["ch"][ch]["sample_size"],
                secinfo["ch"][ch]["fs"],
                secinfo["ch"][ch]["n_ch"]) = bit_parser.__read_chheader__(chsegments[ch])
            except:
                pass
        outinfo[sec] = secinfo
    return outinfo
        
        
        
        



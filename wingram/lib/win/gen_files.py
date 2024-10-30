import os
import glob
from pathlib import Path
import shutil
from ...utils.log import logger

def prepare_files(
    tardir:str,
    overwrite:bool = True,
    ) -> None:
    src = Path(__file__).parent.parent.parent / "stats"

    # tar = glob.glob(tmp)[0]
    
    shutil.copytree(src, tardir, dirs_exist_ok=overwrite)
    # shutil.copy2(tmp+"win.prm", tardir+"/win.prm",file_exists_ok=overwrite)
    return
import os
import numpy as np
from ...utils import *

# #############################################################################
# structure
# #############################################################################
def mkwinstruct(
    lat: float = 35.5,
    lon: float = 139.5,
    dep: float = 30.0,
    vp: list = [5.5 , 5.51, 6.1 , 6.11, 6.7 , 6.71, 8.  , 8.2 ],
    laythick: list = [4.00e+00, 1.00e-02, 1.06e+01, 1.00e-02, 1.69e+01, 1.00e-02, 6.00e+02],
    structname = "ABC",
    unc_t:float = 5.,
    unc_lat:float = 100.,
    unc_lon:float = 100.,
    unc_dep:float = 30.,
    save:bool = False,
    savedir:str = ".",
    savename:str = None,
    **kwargs,
    ):
    """
    winの速度構造を作成して，テキストをreturnする．
    ファイルの保存は出力されるテキストを別途コードを作成して保存すること．
    """
    """
    hypomhが使う速度構造ファイルです。 内容は次のとおりです。FORTRANの書式付き入力なので桁位置は重要です。

    [１行目]初期震源の緯度(°)、経度(°)、深さ(km)(3F10.0)
    [２行目]層の数と構造名(I5,2X,A3)
    [３行目]各層の最上部のP波速度(km/s)(7F10.0)
    [４行目]各層の厚さ(km)(7F10.0)
    [５行目]初期震源の不確定さ （震源時(s)、緯度(km)、経度(km)、深さ(km)）(4F10.0) ただし「初期震源不確定さ」のうちの「震源時(s)」は実際には使われない。
    
    各層はそれぞれ一定の正の速度勾配を持ち、 層の境界で速度は連続になります。S波速度構造は、 Vp/Vs=1.73としてP波速度構造から求められます。
    一番上の層の上面は海抜高度０で、そこから２行目に与えた数の層が あり、その下にさらに通常は厚い層がおかれ、この層の底の速度までが 与えられます（海抜高度０よりも上の部分については、一番上の層が同じ 速度勾配で続いているものとみなされて計算されます）。
    従って、３行目で与えられる「各層の最上部のP波速度」 の数は２行目の「層の数」+2となり、
    ４行目で与えられる「各層の厚さ」の 数は、２行目の「層の数」+1となります。
    なお、３行目と４行目は、 層の数によって実際にはそれぞれ２行以上になることもあります。 初期震源の緯度と経度は、winでは、最も走時の早い観測点の緯度経度を 適当に丸めて作られますので、１行目で与える値は実際には使われません。
    以下に構造ファイルの例を示します。

    35.5      139.5     30.0
        6 ABC
    5.50      5.51      6.10      6.11      6.70      6.71      8.00
    8.20
    4.00      0.01      10.60     0.01      16.90     0.01      600.0
    5.0       100.0     100.0     30.0
    """
    # =============================================================
    # 確認
    # =============================================================
    if len(vp) < 2:
        logger.error(f"list vp should be longer than 2: {len(vp)}")
        return
    if len(laythick) != len(vp) -1:
        logger.error(f"list laythock should be shorter than vp by 1: {len(laythick)}")
        return
    # ===============================================================
    # start
    # =============================================================
    nlay = len(vp) - 2
    text = ""
    
    # 1行目
    text += f"{lat:<10g}{lon:<10g}{dep:<10g}\n"

    # 2行目
    text += f"{nlay:>5.0f}  {structname[:3]:<3}\n"
    # 3行目
    n = 1
    for i in vp:
        text += f"{i:<10g}"
        # text += f"{i:<7.2f}"

        if n >= 7:
            text += "\n"
            n = 1
        else:
            n += 1
    if n != 1:
        text += "\n"
    # 4行目
    n = 1
    for i in laythick:
        text += f"{i:<10g}"
        # text += f"{i:<7.10f}"
        
        if n >= 7:
            text += "\n"
            n = 1
        else:
            n += 1
    if n != 1:
        text += "\n"
    # 5行目
    text += f"{unc_t:<10g}{unc_lat:<10g}{unc_lon:<10g}{unc_dep:<10g}"
    # text += f"{unc_t:<4.10f}{unc_lat:<4.10f}{unc_lon:<4.10f}{unc_dep:<4.10f}"

    
    # -------------------------
    # SAVE
    # -------------------------
    if save:
        savefp = os.path.join(savedir,savename)
        logger.info(f"saving...: {savefp}")
        if not os.path.exists(savedir):
            os.mkdir(savedir)
        with open(savefp, 'w') as f:
            f.write(text)
        logger.info(f"SAVED: {savefp}")
    return text

def jma2stan(fp, outdir = "", save = False, **kwargs):
    """
    JMAの速度構造からwinの速度構造ファイルを作る．
    mkwinstructを使用．
    """
    dat = np.loadtxt(
        fp,
        # delimiter = " ",
        )
    
    out = mkwinstruct(
        vp = dat[:,0],
        # laythick = dat[:-1,2],
        # laythick = [0.5]*(len(dat)-1),
        laythick = np.diff(dat[:,2]),
        structname = os.path.basename(fp),
        **kwargs,
    )
    
    if save:
        outfp = os.path.join(
            outdir,
            f"struct_{os.path.basename(fp)}.tbl"
        )
        
        with open(outfp, 'w') as f:
            f.write(out)
        
    return out

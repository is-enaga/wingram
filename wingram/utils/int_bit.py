import numpy as np
def int2bin(
    value:int,
    nbit:int,
    signed:bool = False,
):
    """
    Convert integer into binary string (big endian).
    """
    # ----------------------
    # check, prepare
    # ----------------------
    if signed:
        # check range -----------
        if not (-2**(nbit-1)<= value <= 2**(nbit-1)-1):
            raise ValueError(f"Value {value} is out of range of {nbit}-bit signed integer: [{-2**(nbit-1)},{2**(nbit-1)-1}]")
        
        # 補数変換 -----------
        if value < 0:
            value = (1 << nbit) + value
    else:
        # check range -----------
        if not (0 <= value <= 2**nbit-1):
            raise ValueError(f"Value {value} is out of range of {nbit}-bit unsigned integer: [0,{2**nbit-1}]")
    
    # ----------------------
    # main
    # ----------------------
    binstr = format(value, f'0{nbit}b')
    
    return binstr

# int2bin関数をベクトル化
intarray2bin = np.vectorize(int2bin)

def bit2signint(bit:str, bitsize:int = None):
    """
    Convert bit string to signed integer.
    Used when read WIN data.
    Args
    ----
    bit: str
        bit string
    bitsize: int
        bit size for conversion to signed integer. 
    """
    if bitsize is None:
        bitsize = len(bit)
    out = int(bit,2)
    if out >= 2**(bitsize-1):
        out -= 2**bitsize
    return out

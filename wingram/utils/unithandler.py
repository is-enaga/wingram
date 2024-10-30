import re

def integrate_unit(unit:str):
    """
    Convert unit string into the unit that can be used in the calculation.
    """
   # 正規表現パターン
    pattern = re.compile(r'(/s)')
    
    # 単位の積分
    if pattern.search(unit):
        # /s を1つ削除
        unit = pattern.sub('', unit, count=1)
    else:
        # *s を追加
        unit += '*s'
    
    return unit

def diff_unit(unit:str):
    """
    Convert unit string into the unit that can be used in the calculation.
    """
    # 正規表現パターン
    pattern = re.compile(r'(\*s)')
    
    # 単位の微分
    if pattern.search(unit):
        # *s を1つ削除
        unit = pattern.sub('', unit, count=1)
    else:
        # /s を追加
        unit += '/s'
    
    return unit
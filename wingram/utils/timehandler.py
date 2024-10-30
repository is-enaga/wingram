def yy2yyyy(yy:int):
    """
    Convert yy of hypomh to yyyy.
    """
    if 70 <= yy <= 99:
        yyyy = yy + 1900
    elif 0 <= yy < 70:
        yyyy = yy + 2000
    else:
        raise ValueError(f"yy is out of expected range 00<=yy<=99: {yy}")
    return yyyy

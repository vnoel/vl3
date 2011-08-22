import numpy as np

def signal_ratio(denum, num, ratio_min=0, ratio_max=10, invalid=-998):

    num2 = np.ma.masked_invalid(num)
    denum2 = np.ma.masked_invalid(denum)

    d = num2 / denum2
    idx = (denum < invalid) | (num < invalid)
    d[idx] = np.nan

    idx = (d < ratio_min) | (d > ratio_max)
    d[idx] = np.nan

    return d

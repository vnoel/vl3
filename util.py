import numpy as np

def signal_ratio(denum, num, ratio_min=0, ratio_max=10, invalid=-998):

    d = num / denum

    idx = (denum < invalid) | (num < invalid) | (d < ratio_min) | (d > ratio_max)
    d[idx] = np.nan

    return d

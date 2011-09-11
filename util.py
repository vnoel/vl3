import numpy as np

def signal_ratio(denum, num, ratio_min=0, ratio_max=10, invalid=-998):

    d = num / denum

    idx = (denum < invalid) | (num < invalid) | (d < ratio_min) | (d > ratio_max)
    d[idx] = np.nan

    return d


def lna_data_merge(lna_data1, lna_data2):
    """
    merge two datasets:
    merge time vectors from both datasets
    merge data arrays present in both datasets
    copy arrays that are only in one dataset
    """


    if lna_data1 is None and lna_data2 is None:
        return None
    elif lna_data1 is None:
        return lna_data2.copy()
    elif lna_data2 is None:
        return lna_data1.copy()
    else:
        lna_data1['time'].extend(lna_data2['time'])
        for key in lna_data1['data']:
            if key in lna_data2['data']:
                # extend data that is in both datasets
                lna_data1['data'][key] = np.append(lna_data1['data'][key], lna_data2['data'][key], axis=0)
        for key in lna_data2['data']:
            if key not in lna_data1['data']:
                # copy data that is just in second data
                lna_data1['data'][key] = lna_data2['data'][key].copy()

        return lna_data1


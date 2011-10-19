import numpy as np

def signal_ratio(denum, num, ratio_min=0, ratio_max=10, invalid=-998):

    d = num / denum

    idx = (denum < invalid) | (num < invalid) | (d < ratio_min) | (d > ratio_max)
    d[idx] = np.nan

    return d


def lidar_data_merge(lidar_data1, lidar_data2):
    """
    merge two datasets:
    merge time vectors from both datasets
    merge data arrays present in both datasets
    copy arrays that are only in one dataset
    """


    if lidar_data1 is None and lidar_data2 is None:
        return None
    elif lidar_data1 is None:
        return lidar_data2.copy()
    elif lidar_data2 is None:
        return lidar_data1.copy()
    else:
        lidar_data1['time'].extend(lidar_data2['time'])
        for key in lidar_data1['data']:
            if key in lidar_data2['data']:
                # extend data that is in both datasets
                lidar_data1['data'][key] = np.append(lidar_data1['data'][key], lidar_data2['data'][key], axis=0)
        for key in lidar_data2['data']:
            if key not in lidar_data1['data']:
                # copy data that is just in second data
                lidar_data1['data'][key] = lidar_data2['data'][key].copy()

        return lidar_data1


def lidar_multiple_files_read(filelist, file_read_function, format):
    filelist.sort()
    fulldata = None
    for f in filelist:
        lidar_data = file_read_function(f, format)
        fulldata = lidar_data_merge(fulldata, lidar_data)

    if fulldata is None:
        return None

    return fulldata

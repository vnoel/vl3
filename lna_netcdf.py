#!/usr/bin/env python
# encoding: utf-8
"""
lna_netcdf.py

Created by Vincent Noel on 2011-08-17.
Copyright (c) 2011 LMD/CNRS. All rights reserved.
"""

import numpy as np
from datetime import datetime
import glob
from util import signal_ratio, lna_data_merge
from scipy.io.netcdf import netcdf_file

    
def lna_netcdf_folder_read(yagfolder):
    
    files = glob.glob(yagfolder + '/*.nc')
    lna_data = lna_netcdf_files_read(files)
    
    return lna_data


def lna_netcdf_files_read(filelist):
    filelist.sort()
    fulldata = None
    for f in filelist:
        print 'Reading ', f
        lna_data = lna_netcdf_file_read(f)
        fulldata = lna_data_merge(fulldata, lna_data)
    
    if fulldata is None:
        return None
    
    return fulldata


def lna_netcdf_file_read(yagfile):
    
    nc = netcdf_file(yagfile)
    
    time = nc.variables['time'][:]
    hour = np.floor(time)
    hourfraction = time - hour
    minutes = np.floor(hourfraction * 60.)
    seconds = hourfraction * 3600 - minutes*60.
    
    date = datetime(nc.year, nc.month, nc.day)
    
    dates = []
    for i in range(len(time)):
        dates.append(datetime(nc.year, nc.month, nc.day, hour[i], minutes[i], seconds[i]))
    
    time = dates
    alt = nc.variables['range'][:]
    
    data = {}
    for variable in nc.variables:
        if variable.startswith('p'):
            var = nc.variables[variable]
            long_name = variable + ': Range-Corrected Backscatter ' + var.wavelength + 'nm '
            if var.polarization != 'NULL':
                long_name += var.polarization + ' '
            long_name += var.telescope
            data[long_name] = nc.variables[variable][:,:].copy()
            idx = data[long_name] == var.missing_value
            data[long_name][idx] = np.nan
    
    data['p7: Depolarization Ratio 532nm NFOV'] = signal_ratio(nc.variables['p1'][:], nc.variables['p2'][:])
    data['p8: Depolarization Ratio 532nm WFOV'] = signal_ratio(nc.variables['p4'][:], nc.variables['p5'][:])
    data['p9: Color Ratio 1064nm/532nm NFOV'] = signal_ratio(nc.variables['p1'][:], nc.variables['p3'][:])
    # data['p10: Color Ratio 1064nm/532nm WFOV'] = ratio(nc.variables['p4'][:], nc.variables['p6'][:])
    
    lna_data = {'time':time, 'alt':alt, 'data':data, 'date':date, 'filetype':'netcdf'}
    nc.close()
    
    return lna_data



import unittest

class test(unittest.TestCase):
    
    def test_nprof(self):
        ncfile = 'test_data/netcdf/lna_1a_PR2_v02_20040319_080000_60.nc'
        lna_data = lna_netcdf_file_read(ncfile)
        time = lna_data['time']
        self.assertEqual(np.shape(time)[0], 27)
    
    def test_nalt(self):
        ncfile = 'test_data/netcdf/lna_1a_PR2_v02_20040319_080000_60.nc'
        lna_data = lna_netcdf_file_read(ncfile)
        alt = lna_data['alt']
        self.assertEqual(np.shape(alt)[0], 1024)


if __name__ == '__main__':
    print 'profiling now'
    import cProfile
    cProfile.run("lna_netcdf_folder_read('test_data/netcdf')", 'profile')
    
    unittest.main()

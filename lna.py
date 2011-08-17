#!/usr/bin/env python
# encoding: utf-8
"""
lna.py

Created by Vincent Noel on 2011-07-14.
Copyright (c) 2011 LMD/CNRS. All rights reserved.
"""

import os
import numpy as np
# I'd rather use netCDF4, but it is not part of EPD Free
# scipy is more frequent
from scipy.io.netcdf import netcdf_file
from datetime import datetime
import glob

import matplotlib.dates as mdates

def find_closest_time(time, timelist):

    deltas = np.abs(time - timelist)
    imin = np.argmin(deltas)
    mindelta = deltas[imin]
            
    return imin, mindelta
    

def data_regrid_time(time, data):
    
    print 'Regridding data on fixed-step time'
    
    delta = time[1] - time[0]
    current = time[0]
    newtime = [time[0]]
    while current < time[-1]:
        current += delta
        newtime.append(current)
        
    numtime = mdates.date2num(time)
    numnewtime = mdates.date2num(newtime)
    numdelta = np.abs(numtime[1] - numtime[0])
    
    newdata = {}
    for k in data.keys():
        print 'Regridding ' + k
        newk = np.empty([len(newtime), np.shape(data[k])[1]])
        iprof = -1
        for i in xrange(len(numnewtime)):
            if (iprof+1) < len(numtime) and np.abs(numnewtime[i] - numtime[iprof+1]) <= numdelta:
                    mindiff = np.abs(numnewtime[i] - numtime[iprof+1])
                    iprof = iprof + 1
            else:
                iprof, mindiff = find_closest_time(numnewtime[i], numtime)
                
            if mindiff > numdelta:
                newk[i, :] = np.nan
            else:
                newk[i, :] = data[k][iprof, :]
        newdata[k] = newk
        
    return newtime, newdata


def open_source(lna_source):
    
    if os.path.isdir(lna_source):
        lna_data = nc_folder_read(lna_source)
    else:
        lna_data = nc_read(lna_source)
        
    return lna_data


def depol(para, perp):

    d = perp / para
    idx = (para < -998) | (perp < -998)
    d[idx] = np.nan

    idx = (d < 0)
    d[idx] = np.nan

    idx = (d > 10)
    d[idx] = np.nan

    idx = (d > 6)
    d[idx] = 6.0

    return d


def nc_folder_read(yagfolder):
    files = glob.glob(yagfolder + '/*.nc')
    files.sort()
    fulldata = None
    for f in files:
        print 'Reading ', f
        lna_data = nc_read(f)
        time = lna_data['time']
        alt = lna_data['alt']
        data = lna_data['data']
        date = lna_data['date']
        
        if fulldata is None:
            fulldata = data
            fulltime = time
        else:
            fulltime.extend(time)
            for key in fulldata:
                fulldata[key] = np.append(fulldata[key], data[key], axis=0)

    if fulldata is None:
        return None
        
    fulltime, fulldata = data_regrid_time(fulltime, fulldata)
    fulllna_data = {'time':fulltime, 'alt':alt, 'data':fulldata, 'date':date}
            
    return fulllna_data
    

def nc_read(yagfile):
    
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
        
    data['p7: Depolarization Ratio 532nm NFOV'] = depol(nc.variables['p1'][:], nc.variables['p2'][:])
    data['p8: Depolarization Ratio 532nm WFOV'] = depol(nc.variables['p4'][:], nc.variables['p5'][:])

    lna_data = {'time':time, 'alt':alt, 'data':data, 'date':date}
    nc.close()
    
    return lna_data
    

import unittest

class test(unittest.TestCase):
    
    def test_nprof(self):
        ncfile = 'test_data/lna_1a_PR2_v02_20040319_080000_60.nc'
        lna_data = nc_read(ncfile)
        time = lna_data['time']
        self.assertEqual(np.shape(time)[0], 27)
        
    def test_nalt(self):
        ncfile = 'test_data/lna_1a_PR2_v02_20040319_080000_60.nc'
        lna_data = nc_read(ncfile)
        alt = lna_data['alt']
        self.assertEqual(np.shape(alt)[0], 1024)
        

if __name__ == '__main__':
    unittest.main()


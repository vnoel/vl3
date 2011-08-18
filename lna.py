#!/usr/bin/env python
# encoding: utf-8
"""
lna.py

Created by Vincent Noel on 2011-07-14.
Copyright (c) 2011 LMD/CNRS. All rights reserved.
"""

import os
import numpy as np
import glob
from lna_bin import lna_binary_file_read, lna_binary_folder_read
from lna_netcdf import lna_netcdf_file_read, lna_netcdf_folder_read

import matplotlib.dates as mdates


def find_closest_time(time, timelist):

    deltas = np.abs(time - timelist)
    imin = np.argmin(deltas)
    mindelta = deltas[imin]
            
    return imin, mindelta
    

def lna_data_regrid_time(lna_data):
    
    # print 'Regridding data on fixed-step time'
    
    time = lna_data['time']
    data = lna_data['data']

    delta = time[1] - time[0]
    # print 'regridding using delta ', delta
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
        # print 'Regridding ' + k
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
        
    lna_data['time'] = newtime
    lna_data['data'] = newdata
    return lna_data


def open_source(lna_source):
    
    if os.path.isdir(lna_source):
        # is it a folder of netcdf or binary data ?
        files = glob.glob(lna_source + '/*.nc')
        if len(files) > 0:
            lna_data = lna_netcdf_folder_read(lna_source)
        else:
            lna_data = lna_binary_folder_read(lna_source)
            
    else:
        # is it a file of netcdf or binary data ?
        if '.nc' in lna_source:
            lna_data = lna_netcdf_file_read(lna_source)
        else:
            lna_data = lna_binary_file_read(lna_source)

    lna_data = lna_data_regrid_time(lna_data)
        
    return lna_data



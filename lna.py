#!/usr/bin/env python
# encoding: utf-8
"""
lna.py

Created by Vincent Noel on 2011-07-14.
Copyright (c) 2011 LMD/CNRS. All rights reserved.

This module contains the function 
open_source(source)
which opens a file or a folder of files.

The function finds out the format of files
(either binary lna or netcdf) and calls the
appropriate functions from lna_bin and lna_netcdf.

After loading the data, it is regridded on a new time vector
with constant time-step (to fill gaps in the data)

"""

import os
import numpy as np
import glob
from lna_bin import lna_binary_file_read, lna_binary_folder_read
from lna_netcdf import lna_netcdf_file_read, lna_netcdf_folder_read

import matplotlib.dates as mdates


def _find_closest_time(time, timelist):

    deltas = np.abs(time - timelist)
    imin = np.argmin(deltas)
    mindelta = deltas[imin]
            
    return imin, mindelta
    

def _lna_data_regrid_time(lna_data):
    
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
                iprof, mindiff = _find_closest_time(numnewtime[i], numtime)
                
            if mindiff > numdelta:
                newk[i, :] = np.nan
            else:
                newk[i, :] = data[k][iprof, :]
        newdata[k] = newk
        
    lna_data['time'] = newtime
    lna_data['data'] = newdata
    return lna_data


def _source_type(source):
    folder = False
    netcdf = False

    if os.path.isdir(source):
        folder = True
        files = glob.glob(source + '/*.nc')
        if len(files) > 0:
            netcdf = True
    else:
        if source.endswith('.nc'):
            netcdf = True
    return folder, netcdf


def open_source(lna_source):
    """
    
    opens a file or a folder of files.
    
    finds out the format of files
    (either binary lna or netcdf) and calls the
    appropriate functions from lna_bin and lna_netcdf.
    
    afterwards call the regrid function to regrid the
    data on a new time vector with constant time-step.
    
    """
    
    folder, netcdf = _source_type(lna_source)
    if folder:
        if netcdf:
            lna_data = lna_netcdf_folder_read(lna_source)
        else:
            lna_data = lna_binary_folder_read(lna_source)
    else:
        if netcdf:
            lna_data = lna_netcdf_file_read(lna_source)
        else:
            lna_data = lna_binary_file_read(lna_source)

    lna_data = _lna_data_regrid_time(lna_data)
        
    return lna_data


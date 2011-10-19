#!/usr/bin/env python
#encoding: utf-8

"""
lidardata.py

VNoel 2011-10-19

This module contains function to open lidar data files in various
formats and from various instruments.

File formats must be either lna binary (special case) or netcdf.
The variables to read in netcdf files are described in a "ini" file

"""

import os
import glob
from lna_bin import lna_binary_file_read, lna_binary_folder_read
from lidarnetcdf import lidar_netcdf_file_read, lidar_netcdf_folder_read
import matplotlib.dates as mdates
import numpy as np

supported_formats = ['lna', 'als450']


def datafile_format(datafile):
    if datafile.startswith('lna_0a_raw') and datafile.endswith('.dat'):
        # special case for lna binary format
        dataformat = 'lnabinary'
        return dataformat
    else:
        basefile = os.path.basename(datafile)
        if basefile.endswith('.nc'):
            # netcdf format.
            dataformat = basefile.split('_')[0]
            if dataformat in supported_formats:
                return dataformat
    return None


def source_identify(source):
    '''
    Finds out the type of data in a given source
    source is a string containing either a file or a folder path.
    
    returns a tuple : (folder = True/False, format = string)
    format can be either "lnabinary", or one of the "supported_formats" for netcdf files : lna, als
    '''
    
    folder = False
    if os.path.isdir(source):
        folder = True
        files = glob.glob(folder)
        format = None
        while format is None:
            format = datafile_format(files.pop())
    else:
        format = datafile_format(source)

    return folder, format
    
    
def _find_closest_time(time, timelist):

    deltas = np.abs(time - timelist)
    imin = np.argmin(deltas)
    mindelta = deltas[imin]

    return imin, mindelta


def _data_regrid_time(lna_data):

    time = lna_data['time']
    data = lna_data['data']

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
    
def data_from_source(source):
    
    folder, format = source_identify(source)
    if format is None:
        data = None
        
    if format == 'lnabinary':
        # special-case the lna binary file format
        if folder:
            data = lna_binary_folder_read(source)
        else:
            data = lna_binary_file_read(source)

    else:
        # general case netcdf format
        if folder:
            data = lidar_netcdf_folder_read(source, format)
        else:
            data = lidar_netcdf_file_read(source, format)
            
    data = _data_regrid_time(data)
    
    return data
    
    
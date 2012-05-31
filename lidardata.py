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
from util import read_supported_formats


supported_formats = read_supported_formats()


class InvalidFormat(Exception):
    pass


class InvalidFolder(InvalidFormat):
    pass
    

class InvalidFile(InvalidFormat):
    pass
    

class LidarData(object):
    
    '''
    LidarData class
    contains data that wants to be plotted.
    
    '''
    
    def __init__(self, from_source=None):

        if from_source:
            folder, format = source_identify(from_source)
            if format is None:
                if folder:
                    raise InvalidFolder('This folder does not contain files of known format. Valid formats : ' + str(supported_formats))
                else:
                    raise InvalidFile('This file is not of a known format. Valid formats : ' + str(supported_formats))

            if format == 'lnabinary':
                # special-case the lna binary file format
                if folder:
                    data = lna_binary_folder_read(from_source)
                else:
                    data = lna_binary_file_read(from_source, format)

            else:
                # general case netcdf format
                if folder:
                    data = lidar_netcdf_folder_read(from_source, format)
                else:
                    data = lidar_netcdf_file_read(from_source, format)

            self.data = data['data']
            self.datetime = data['time']
            self.alt = data['alt']
            self.date = data['date']
            self.filetype = data['filetype']
            self.data_source = from_source
            self.alt_range = (np.min(self.alt), np.max(self.alt))
            
            data = self._data_regrid_time()
                    
            self.epochtime = mdates.num2epoch(mdates.date2num(self.datetime))
            self.epochtime_range = np.min(self.epochtime), np.max(self.epochtime)
            
            for dataname in self.data:
                assert self.data[dataname].shape[0] == np.shape(self.datetime)[0]


    def _data_regrid_time(self):

        time = self.datetime
        data = self.data

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

        self.datetime = newtime
        self.data = newdata
        

def datafile_format(datafile):
    basefile = os.path.basename(datafile)
    if basefile.startswith('lna_0a_raw') and basefile.endswith('.dat'):
        # special case for lna binary format
        dataformat = 'lnabinary'
        return dataformat
    elif basefile.endswith('.nc'):
        # netcdf format.
        for dataformat in supported_formats:
            if basefile.startswith(dataformat):
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
        files = glob.glob(source + '/*')
        format = None
        while files and (format is None):
            format = datafile_format(files.pop())
        if format:
            print 'Source is folder, datatype ' + format
    else:
        format = datafile_format(source)
        if format:
            print 'Source is file, datatype ' + format

    return folder, format
    
    
def _find_closest_time(time, timelist):

    deltas = np.abs(time - timelist)
    imin = np.argmin(deltas)
    mindelta = deltas[imin]

    return imin, mindelta

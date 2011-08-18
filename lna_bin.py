#!/usr/bin/env python
# encoding: utf-8
"""
lna_bin.py

Created by Vincent Noel on 2011-08-17.
Copyright (c) 2011 LMD/CNRS. All rights reserved.
"""

import numpy as np
from datetime import datetime
import glob


def ratio(denum, num):

    d = num / denum
    idx = (denum < -998) | (num < -998)
    d[idx] = np.nan

    idx = (d < 0)
    d[idx] = np.nan

    idx = (d > 10)
    d[idx] = np.nan

    return d


def lna_binary_folder_read(lnafolder, fov_type='NF'):
    
    # NF
    files = glob.glob(lnafolder + '/lna_0a_raw' + fov_type + '_*.dat')
    files.sort()
    fulldata = None
    
    for f in files:
        lna_data = lna_binary_file_read(f)
        time = lna_data['time']
        alt = lna_data['alt']
        data = lna_data['data']
        date = lna_data['date']
        if fulldata is None:
            fulldata = data.copy()
            fulltime = time
        else:
            fulltime.extend(time)
            for key in data:
                fulldata[key] = np.append(fulldata[key], data[key], axis=0)
                
    if fulldata is None:
        return None
        
    full_lna_data = {'time':fulltime, 'alt':alt, 'data':fulldata, 'date':date, 'filetype':'binary'}
    return full_lna_data


def fix_channel_names(names):
    # we need this because some channel names are fucked up
    newnames = []
    for name in names:
        newname = ''.join(c for c in name if ord(c)<128)
        newnames.append(newname)
    return newnames
    
    
def improve_channel_names(names, fov_type):
    newnames = []
    for name in names:
        if name.startswith('532') or name.startswith('1,06'):
            newname = 'Range-Corrected Backscatter '
            if name.startswith('532'):
                newname = newname + '532nm '
            elif name.startswith('1,06'):
                newname = 'p2 - ' + newname + '1064nm '
                
            if 'paral' in name:
                newname = 'p1 - ' + newname
            elif 'perp' in name:
                newname = 'p3 - ' + newname + 'crosspol '
            newname = newname + fov_type
        else:
            newname = None
        newnames.append(newname)
    return newnames
        

def cut_off_high_altitudes(r, data, max_alt=15.):
    idx = (r < 15.)
    for key in data:
        data[key] = data[key][:,idx]
    r = r[idx]
    return r, data
    
def lna_binary_file_read(lnafile):
    
    time, r, p, b, channels, fov = lna_bin_read(lnafile)
    nchannels = len(channels)
    
    # correct for noise and square distance
    pmbr2 = [np.zeros_like(p[i], dtype='f4') for i in range(nchannels)]     # signal minus noise, range-corrected
    for i in range(nchannels):
        if p[i].shape[1] < 2:
            continue
        nprof = p[i].shape[0]
        for j in range(nprof):
            pmb = p[i][j,:] - b[i]
            pmbr2[i][j,:] = pmb * r * r

    channels = improve_channel_names(channels, fov)
        
    # create data dictionary
    data = {}
    for j in range(nchannels):
        if channels[j] is not None:
            data[channels[j]] = pmbr2[j] * 1e-11
            
    # remove high altitudes
    r /= 1e3
    r, data = cut_off_high_altitudes(r, data)

    # add depolarization
    namepara = 'p1 - Range-Corrected Backscatter 532nm '+fov
    nameperp = 'p3 - Range-Corrected Backscatter 532nm crosspol '+fov
    depol532 = ratio(data[namepara], data[nameperp])
    data['p4 - Depolarization Ratio 532nm ' + fov] = depol532
    # add color ratio
    total532 = data[namepara] + data[nameperp]
    cr = ratio(total532, data['p2 - Range-Corrected Backscatter 1064nm '+fov])
    data['p5 - Color Ratio 1064nm / 532nm ' + fov] = cr
    
    lna_data = {'time':time, 'alt':r, 'data':data, 'date':time[0], 'filetype':'binary'}
        
    return lna_data
    
    
def lna_bin_read(lnafile, debug=False):
    """
    Reads all the data from a SIRTA LNA binary file.
    parameters:
        lnafile - name of the LNA data file
        debug - if True, prints out information durin read
    output:
        time - vectors of datetime objects (nprof)
        r - vector of vertical altitude range (npoints)
        p - arrays of lidar power (integer, arbitrary units) (nprof * npoints)
            arranged as a list by channel number
            e.g. p[5][:,:] is the lidar power array of channel #5
            this is because channels don't necessarily have the same number of points
        b - list of vectors of profile noise level (nprof)
            e.g. b[5][:] is the profile noise vector of channel 5
        intitules - list of names for channels (nchannels)
        fov_type - either WF or NF
    """
    
    f = open(lnafile, 'r')
    
    # ASCII header
    # read the first line, split it in fields
    line = f.readline()
    words = line.split()
    nlines_header = int(words[0][1:])
    # skip the rest of the header
    for i in range(1,nlines_header):
        line = f.readline()
    
    # binary header
    # variable names follow sirta conventions
    nprof, systeme, freq = np.fromfile(file=f, dtype='<i4', count=3)
    nprof -= 1      # first profile is noise data
    fov_type = 'WF' if (systeme==1) else 'NF'
    
    resotemp, resospace = np.fromfile(file=f, dtype='<f4', count=2)
    pretrig, moy, moybruit, nvoies = np.fromfile(file=f, dtype='<i4', count=4)
    intitules = np.fromfile(file=f, dtype='<S10', count=nvoies)

    npoints = np.fromfile(file=f, dtype='<i4', count=nvoies)
    codages = np.fromfile(file=f, dtype='<i4', count=nvoies)
    gains = np.fromfile(file=f, dtype='<f4', count=nvoies)
    offsets = np.fromfile(file=f, dtype='<f4', count=nvoies)
    gains_externes = np.fromfile(file=f, dtype='<f4', count=nvoies)
    offsets_externes = np.fromfile(file=f, dtype='<f4', count=nvoies)
    reserve = np.fromfile(file=f, dtype='i1', count=128)

    if debug:
        print 'n voies: ', nvoies
        print 'n profiles : ', nprof
        print 'intitules voies : ', intitules
        print 'npoints : ', npoints

    # altitude range, converted from m to km
    maxpoints = np.max(npoints)
    r = np.r_[0:maxpoints] * resospace

    # first profile, noise data
    b = [np.zeros(npoints[i]) for i in range(nvoies)]
    # read 6 fields for time, unused
    d, m, y, hh, mm, ss = np.fromfile(file=f, dtype='<u2', count=6)
    # read noise data
    for j in range(nvoies):
        data = np.fromfile(file=f, dtype='<i2', count=npoints[j])
        b[j] = -(data - np.mean(data[-200:]))
        
    # actual data

    p = [np.zeros([nprof, n]) for n in npoints]
    time = []
    for i in range(nprof):
        d, m, y, hh, mm, ss = np.fromfile(file=f, dtype='<u2', count=6)
        time.append(datetime(y,m,d,hh,mm,ss))
            
        for j,n in enumerate(npoints):
            if n>0:
                data = np.fromfile(file=f, dtype='<i2', count=n)
                # store profile data corrected for average bias           
                p[j][i,:] = -(data - np.mean(data[-200:]))
             
    return time, r, p, b, intitules, fov_type
                

import unittest

class test(unittest.TestCase):
    
    def test_file(self):
        testfile = 'test_data/binary/20110705/lna_0a_rawNF_v01_20110705_065026_31.dat'
        lna_data = lna_binary_file_read(testfile)
        time = lna_data['time']
        self.assertEqual(len(time), 180)
        
    def test_folder(self):
        testfolder = 'test_data/binary/20110705'
        lna_data = lna_binary_folder_read(testfolder)
        time = lna_data['time']
        self.assertEqual(len(time), 1440)
    

if __name__ == '__main__':    
    unittest.main()

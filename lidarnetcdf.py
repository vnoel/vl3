#!/usr/bin/env python
#encoding: utf-8

import glob
from scipy.io.netcdf import netcdf_file
import numpy as np
from datetime import datetime
from util import signal_ratio
import json


f = open('dataformats', 'r')
formats = json.load(f)
lidar_variables = formats['lidar_variables']
lidar_ratios = formats['lidar_ratios']


def lidar_netcdf_folder_read(source, format):
    # files = glob.glob(source + '/*.nc')
    # lidar_data = lidar_multiple_files_read(files, format, lidar_netcdf_file_read)
    # return lidar_data
    return None
    
    
def read_variable(nc, varproperties):
    '''
    finds a variable in a netcdf file based on requested properties
    '''
    
    for varname in nc.variables:
        netcdfvar = nc.variables[varname]
        found = []
        for prop in varproperties:
            if prop not in netcdfvar.__dict__:
                found.append(False)
            else:
                if netcdfvar.__dict__[prop] == varproperties[prop]:
                    found.append(True)
                else:
                    found.append(False)
        if all(found):
            variable = netcdfvar[:,:].copy()

            idx = (variable==netcdfvar.missing_value)
            variable[idx] = np.nan

            return variable
    
    
def lidar_netcdf_file_read(source, format):
    
    nc = netcdf_file(source)
    
    time = nc.variables['time'][:]
    hour = np.floor(time)
    hourfraction = time - hour
    minutes = np.floor(hourfraction * 60.)
    seconds = hourfraction * 3600 - minutes * 60.

    date = datetime(nc.year, nc.month, nc.day)
    
    dates = []
    for i in range(len(time)):
        dates.append(datetime(nc.year, nc.month, nc.day, hour[i], minutes[i], seconds[i]))
        
    time = dates
    
    alt = nc.variables['range'][:]
    
    lidar_data = {}
    for variable in lidar_variables[format]:
        properties = lidar_variables[format][variable]
        lidar_data[variable] = read_variable(nc, properties)
    
    for ratio in lidar_ratios[format]:
        num_name = lidar_ratios[format][ratio]['numerator']
        denum_name = lidar_ratios[format][ratio]['denominator']
        lidar_data[ratio] = signal_ratio(lidar_data[denum_name], lidar_data[num_name])
    
    data = {'time':time, 'alt':alt, 'data':lidar_data, 'date':date, 'filetype':'netcdf', 'instrument':format}
    
    return data
                
        
    
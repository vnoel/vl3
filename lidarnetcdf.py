#!/usr/bin/env python
#encoding: utf-8

import glob
from scipy.io.netcdf import netcdf_file
import numpy as np
from datetime import datetime
from util import signal_ratio, lidar_multiple_files_read, read_formats


lidar_variables, lidar_ratios = read_formats()


def lidar_netcdf_folder_read(source, format):
    files = glob.glob(source + '/*.nc')
    lidar_data = lidar_multiple_files_read(files, lidar_netcdf_file_read, format)
    return lidar_data
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
            
    print 'Error : Could not find in netcdf file variable with properties', varproperties
    
    
def lidar_netcdf_file_read(source, format):
    
    nc = netcdf_file(source)
    
    time = nc.variables['time'][:]
    hour = np.floor(time)
    hourfraction = time - hour
    minutes = np.floor(hourfraction * 60.)
    seconds = hourfraction * 3600 - minutes * 60.

    y = nc.year
    m = nc.month
    d = nc.day
    # bug in ALS data
    if d > 1900:
        y, d = d, y
    date = datetime(y, m, d)
    
    dates = []
    for i in range(len(time)):
        dates.append(datetime(y, m, d, hour[i], minutes[i], seconds[i]))
        
    time = dates
    
    alt = nc.variables['range'][:]
    if np.max(alt) > 1000:
        alt = alt / 1000.
    
    lidar_data = {}
    for variable in lidar_variables[format]:
        properties = lidar_variables[format][variable]
        lidar_data[variable] = read_variable(nc, properties)
        
    nc.close()
    
    if format in lidar_ratios:
        for ratio in lidar_ratios[format]:
            num_name = lidar_ratios[format][ratio]['numerator']
            denum_name = lidar_ratios[format][ratio]['denominator']
            lidar_data[ratio] = signal_ratio(lidar_data[denum_name], lidar_data[num_name])
    
    data = {'time':time, 'alt':alt, 'data':lidar_data, 'date':date, 'filetype':'netcdf', 'instrument':format}
    
    return data
                
        
    
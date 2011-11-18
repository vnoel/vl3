#!/usr/bin/env python
#encoding: utf-8

import glob
from scipy.io.netcdf import netcdf_file
import numpy as np
from datetime import datetime
from util import signal_ratio, lidar_multiple_files_read, read_formats, read_supported_vertical_variables

# contains the format definitions
lidar_variables, lidar_ratios = read_formats()
vertical_variables = read_supported_vertical_variables()

def find_vertical_variable(nc):
    for varname in nc.variables:
        if varname in vertical_variables:
            return varname
    return None
    

def lidar_netcdf_folder_read(source, format):
    files = glob.glob(source + '/' + format + '*.nc')
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
            variable = np.array(netcdfvar[:,:].copy(), dtype=np.float16)

            if hasattr(netcdfvar, 'missing_value'):
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

    if hasattr(nc, 'year'):
        y = nc.year
        m = nc.month
        d = nc.day
    else:
        print 'This netcdf file has not global attribute year'
        print 'setting default date as 2006, 1, 1'
        y, m, d = 2006,1,1

    # bug in ALS data
    if d > 1900:
        y, d = d, y
        
    date = datetime(y, m, d)
    
    dates = []
    for i in range(len(time)):
        dates.append(datetime(y, m, d, hour[i], minutes[i], seconds[i]))
        
    time = dates
    
    vertical_varname = find_vertical_variable(nc)
    print 'Found vertical variable : ', vertical_varname
    if vertical_varname is None:
        # we have a problem
        return None
        
    alt = nc.variables[vertical_varname][:]
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
        has_ratio = True
    else:
        has_ratio = False
    
    data = {'time':time, 'alt':alt, 'data':lidar_data, 'date':date, 'filetype':'netcdf', 'instrument':format, 'has_ratio':has_ratio}
    
    return data
                
        
    
#!/usr/bin/env python
#encoding: utf-8

import glob
from scipy.io.netcdf import netcdf_file
import numpy as np
from datetime import datetime
from util import signal_ratio


lidar_variables = {
'lna': 
    {
    '1: Pr2 532nm parallel NFOV':
        {'long_name':'Apparent (not normalized) range-corrected back-scattered power (P*R*R)',
         'wavelength':'532',
         'polarization':'NULL',
         'telescope':'NFOV'
         },
    '2: Pr2 532nm crosspol NFOV':
        {'long_name':'Apparent (not normalized) range-corrected back-scattered power (P*R*R)',
        'wavelength':'532',
        'polarization':'crosspol',
        'telescope':'NFOV'
        },
    '3: Pr2 1064nm NFOV':
        {'long_name':'Apparent (not normalized) range-corrected back-scattered power (P*R*R)',
        'wavelength':'1064',
        'polarization':'NULL',
        'telescope':'NFOV'
        },
    '4: Pr2 532nm parallel WFOV':
        {'long_name':'Apparent (not normalized) range-corrected back-scattered power (P*R*R)',
        'wavelength':'532',
        'polarization':'NULL',
        'telescope':'WFOV'
        },
    '5: Pr2 532nm crosspol WFOV':
        {'long_name':'Apparent (not normalized) range-corrected back-scattered power (P*R*R)',
        'wavelength':'532',
        'polarization':'crosspol',
        'telescope':'WFOV'
        }
    },
    
'als450':
    {
    '1: Pr2 355nm parallel':
        {'long_name':'Apparent (not normalized) range-corrected back-scattered power (P*R*R)',
         'wavelength':'355',
         'polarization':'NULL'
        },
    '2: Pr2 355nm crosspol':
        {'long_name':'Apparent (not normalized) range-corrected back-scattered power (P*R*R)',
         'wavelength':'355',
         'polarization':'crosspol'
        }    
    }
}

lidar_ratios = {
'lna':
    {
    '1: Depolarization Ratio 532nm NFOV': 
        {'numerator':'2: Pr2 532nm crosspol NFOV', 'denominator':'1: Pr2 532nm parallel NFOV'},
    '2: Depolarization Ratio 532nm WFOV':
        {'numerator':'5: Pr2 532nm crosspol WFOV', 'denominator':'4: Pr2 532nm parallel WFOV'},
    '3: Color Ratio':
        {'numerator':'3: Pr2 1064nm NFOV', 'denominator':'1: Pr2 532nm parallel NFOV'}
    }
}

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
        print 'Reading ' + variable
        lidar_data[variable] = read_variable(nc, properties)
    
    for ratio in lidar_ratios[format]:
        num_name = lidar_ratios[format][ratio]['numerator']
        denum_name = lidar_ratios[format][ratio]['denominator']
        lidar_data[ratio] = signal_ratio(lidar_data[denum_name], lidar_data[num_name])
    
    data = {'time':time, 'alt':alt, 'data':lidar_data, 'date':date, 'filetype':'netcdf', 'instrument':format}
    
    return data
                
        
    
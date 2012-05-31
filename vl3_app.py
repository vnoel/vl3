#!/usr/bin/env python
# encoding: utf-8

"""
vl3_app.py

Created by Vincent Noel on 2011-07-18.
Copyright (c) 2011 LMD/CNRS. All rights reserved.

This is the main program for the vl3 application.
Takes care of creating menus and stuff.
"""


import numpy as np
import os, sys

from rhi import Rhi
from controller import RhiController

from util import print_supported_formats
from config import major_version, minor_version

    
if __name__ == '__main__':
    
    np.seterr(all='ignore')

    print 'vl3 - v.%d.%3.1f' % (major_version, minor_version)
    print_supported_formats()
    
    datafile = None

    if 'pistachio' in os.uname()[1]:
        datafile = '/Users/vnoel/Code/vl3_test_data/netcdf/lna_1a_PR2_v02_20040319_100000_60.nc'
    
    if len(sys.argv) > 1:
        datafile = sys.argv[1]
    
    rhi = Rhi(datafile)
    controller = RhiController(view=rhi)
    rhi.configure_traits(handler=controller)

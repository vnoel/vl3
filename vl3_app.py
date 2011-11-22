#!/usr/bin/env python
# encoding: utf-8

"""
vl3_app.py

Created by Vincent Noel on 2011-07-18.
Copyright (c) 2011 LMD/CNRS. All rights reserved.

This is the main program for the vl3 application.
Takes care of creating menus and stuff.
"""


import sys

from imageplot import ImagePlot
from imageplot import minor_version, major_version
from controller import ImagePlotController

from util import read_supported_formats


def print_supported_formats():
    
    supported_formats = read_supported_formats()
    print 'Supported data formats :'
    for key in supported_formats:
        print '\t'+key
    print '\tlna_0a'
    
    
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        yagfile = sys.argv[1]
    else:
        yagfile = None
    
    print 'vl3 - v.%d.%d' % (major_version, minor_version)
    print_supported_formats()
    
    imageapp = ImagePlot(yagfile)
    controller = ImagePlotController(view=imageapp)
    imageapp.configure_traits(handler=controller)
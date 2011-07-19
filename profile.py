#!/usr/bin/env python
# encoding: utf-8
"""
profile.py

Created by Vincent Noel on 2011-07-15.
Copyright (c) 2011 LMD/CNRS. All rights reserved.
"""

import numpy as np
import chaco.api as chaco

from traits.api import HasTraits, Instance, Button, Bool, Enum, List, Str
from traitsui.api import Item, UItem, View, HGroup, VGroup, Handler
from enable.api import ComponentEditor


class ProfileHandler(Handler):
    def close(self, info, is_ok):
        if info.object.parent is not None:
            info.object.parent.profileplot = None
        # info.object.parent.img.overlays.remove(info.object.parent.line_inspector)
        return Handler.close(self, info, is_ok)
    
class ProfilePlot(HasTraits):
    
    profileplot = Instance(chaco.Plot)
    
    traits_view = View(
        VGroup(
            UItem('profileplot', width=300, height=500, editor=ComponentEditor()),
        ),
        resizable=True,
        title='Profile',
        handler=ProfileHandler
    )
        
    def __init__(self, parent, profiledata=None, alt=None, profname=None):
        
        self.data = chaco.ArrayPlotData()
        self.data.set_data('value', [])
        self.data.set_data('index', [])
        
        plot = chaco.Plot(self.data, orientation='v')
        plot.plot(('index', 'value'), name='profile')
        plot.y_axis.title = 'Altitude [km]'
        self.profileplot = plot
        if parent:
            plot.value_range = parent.img.color_mapper.range
            plot.index_range = parent.img.y_mapper.range
        self.parent = parent
        if profiledata is not None and alt is not None and profname is not None:
            self.set_profile(profiledata, alt, profname)
            
    def set_profile(self, profiledata, alt, profname):        

        self.data.set_data('index', alt)
        self.data.set_data('value', profiledata)
        self.profiledata = profiledata
        self.profileplot.title = 'Profile ' + str(profname)
                
                
if __name__ == '__main__':
    '''
    Show some stuff as a test
    '''
    import yag
    import numpy as np
    
    datetime, alt, data, date = yag.nc_folder_read('test_data/')
    seldata = data.keys()[0]
    profileplot = ProfilePlot(None)
    profile_data = data[seldata][:,0]
    profileplot.set_profile(profile_data, alt, seldata)
    profileplot.configure_traits()
    
    
    
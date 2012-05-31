#!/usr/bin/env python
# encoding: utf-8
"""
profile.py

Created by Vincent Noel on 2011-07-15.
Copyright (c) 2011 LMD/CNRS. All rights reserved.
"""

import chaco.api as chaco

from traits.api import HasTraits, Instance
from traitsui.api import UItem, View, VGroup, Handler
from enable.api import ComponentEditor


class ProfilePlot(HasTraits):
    
    profileplot = Instance(chaco.Plot)
    
    traits_view = View(
        VGroup(
            UItem('profileplot', width=300, height=500, editor=ComponentEditor()),
        ),
        resizable=True,
        title='Profile',
    )
        
    def __init__(self, parent, profiledata=None, alt=None, profname=None):
        
        self.data = chaco.ArrayPlotData()
        self.data.set_data('value', [])
        self.data.set_data('index', [])
        
        plot = chaco.Plot(self.data, orientation='v')
        plot.plot(('index', 'value'), name='profile')
        plot.y_axis.title = 'Altitude [km]'
        plot.x_axis.title = 'Signal'
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
        
        
    def save_image(self, save_image_file):
        
        window_size = self.profileplot.outer_bounds
        print window_size
        gc = chaco.PlotGraphicsContext([window_size[0]+1, window_size[1]+1])
        gc.render_component(self.profileplot)
        gc.save(save_image_file)
        

        
class ProfileController(Handler):

    view = Instance(ProfilePlot)

    def init(self, info):
        self.view = info.object

    def close(self, info, is_ok):
        if self.view.parent is not None:
            self.view.parent.profileplot = None
        # info.object.parent.img.overlays.remove(info.object.parent.line_inspector)
        return Handler.close(self, info, is_ok)       



if __name__ == '__main__':
    '''
    Show some stuff as a test
    '''
    # import lna
    # 
    # datetime, alt, data, date = lna.nc_folder_read('test_data/netcdf/')
    # seldata = data.keys()[0]
    # profileplot = ProfilePlot(None)
    # profile_data = data[seldata][:,0]
    # profileplot.set_profile(profile_data, alt, seldata)
    # profileplot.configure_traits()
    
    
    
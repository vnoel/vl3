#!/usr/bin/env python
# encoding: utf-8
"""
imageplot.py

Created by Vincent Noel on 2011-07-18.
Copyright (c) 2011 LMD/CNRS. All rights reserved.

ImagePlot class for lidar curtain plot.
This is where the real work of data display takes place in the
vl3 application.

This script can also be used standalone :
    imageplot.py LNA_FOLDER
    or 
    imageplot.py LNA_FILE
but menu items most likely won't work.
"""

import sys
import os
import numpy as np
import chaco.api as chaco
from chaco.tools.api import LineInspector, ZoomTool

from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator

from traits.api import HasTraits, Instance, Button, Bool, Enum, List, Str
from traitsui.api import Item, UItem, View, HGroup
from traitsui.menu import Menu, MenuBar, CloseAction, Action, Separator
from enable.api import ComponentEditor

from pyface.api import MessageDialog, ImageResource

import matplotlib.dates as mdates

from lidardata import data_from_source
from profile import ProfilePlot, ProfileController

basesirta_path = '/bdd/SIRTA/'

major_version = 0
minor_version = 3

# change factor for colormap caxis
cmap_change_factor = 1.5


def add_date_axis(plot):
    bottom_axis = chaco.PlotAxis(plot, orientation='bottom', tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
    plot.underlays.append(bottom_axis)


class ImagePlot(HasTraits):
    
    data_source = ''
    data_list = List([])
    plot_title = Str('')
    window_title = Str('View Lidar 3 v%d.%d' % (major_version, minor_version))
    
    icon_img = ImageResource('icon', search_path=[os.getcwd()+'/', './', '/users/noel/vl3/', sys.path[0]])
    
    data_type = Enum('Pr2', 'Ratio')
    seldata = Enum(values='data_list')
    container = Instance(chaco.HPlotContainer)
    show_profile = Button('Show profile')
    log_scale = Bool
    reset_zoom = Button('Reset Zoom')
    scale_more = Button('Scale++')
    scale_less = Button('Scale--')

    traits_view = View(
        HGroup(
            UItem('data_type', visible_when=''),
            UItem('seldata', springy=True),
            visible_when='plot_title != ""'
        ),
        UItem('container', width=800, height=300, editor=ComponentEditor()),
        HGroup(
            UItem('show_profile'),
            UItem('reset_zoom'),
            UItem('scale_less'),
            UItem('scale_more'),
            Item('log_scale', label='Log Scale', visible_when='"Backscatter" in data_type'),
            visible_when='plot_title != ""'
        ),
        menubar=MenuBar(
            Menu(
                CloseAction,
                Separator(),
                Action(name='Open directory (LNA/ALS)...', action='open_dir'),
                Action(name='Open LNA/ALS file...', action='open_file'),
                Action(name='Save Plot...', action='save'),
                name='File',
            ),
            Menu(
                Action(name='New view', action='new_view'),
                Action(name='New empty view', action='new_empty_view'),
                name='View',
            ),
            Menu(
                Action(name='About', action='about_dialog'),
                name='Help'
            ),
        ),
        resizable=True,
        title=str(window_title),
        icon=icon_img
    )
    
    
    def __init__(self, data_source=None, base_folder=basesirta_path):
        
        self.pcolor = None
        self.pcolor_data = None
        self.profileplot = None

        self.save_image_file = os.getcwd()

        if data_source is None:
            if os.path.isdir(base_folder):
                self.directory_to_load = base_folder
            else:
                self.directory_to_load = os.getcwd()
        else:
            if os.path.isdir(data_source):
                self.directory_to_load = data_source
            else:
                self.directory_to_load = os.path.dirname(data_source)
            
            self.open_data(data_source)
                

    def update_window_title(self):
        self.window_title = 'View Lidar 3 v%d.%d' % (major_version, minor_version) + ' - ' + str(self.date.date())
        

    def make_plot_title(self):
        return str(self.date.date()) + ' : ' + self.seldata        
        
        
    def open_data(self, data_source):
        
        if data_source is None:
            return
            
        print 'Log: opening ', data_source
        lidardata = data_from_source(data_source)

        if lidardata is None:
            msg = MessageDialog(message="No LNA data found in this folder.", severity='warning', title='Problem')
            msg.open()
            return
                
        self.datetime = lidardata['time']
        self.alt = lidardata['alt']
        self.data = lidardata['data']
        self.date = lidardata['date']
        self.data_source = data_source

        self.alt_range = np.min(self.alt), np.max(self.alt)

        epochtime = mdates.num2epoch(mdates.date2num(self.datetime))
        self.epochtime_range = np.min(epochtime), np.max(epochtime)

        self.data_type = 'Pr2'

        self.update_data_list()
        self.seldata = self.data_list[0]

        self.plot_title = self.make_plot_title()
        self.update_window_title()
        self.pcolor, self.container = self.pcolor_create()
                
        
    def update_data_list(self):
        
        data_list = []
        for key in self.data.keys():
            if self.data_type in key:
                data_list.append(key)
        data_list.sort()
        self.data_list = data_list
        
        
    def pcolor_create(self):
        
        data = chaco.ArrayPlotData()

        data.set_data('image', self.data[self.seldata].T)
        self.pcolor_data = data
        
        self.cmin = np.nanmin(self.data[self.seldata])
        self.cmax = np.nanmax(self.data[self.seldata])
        
        plot = chaco.Plot(data, padding=40)

        # DON'T FORGET THE [0] to get a handle to the actual plot
        img = plot.img_plot('image', name=self.plot_title, colormap=chaco.jet,
                            xbounds=self.epochtime_range,
                            ybounds=self.alt_range)[0]
        img.overlays.append(ZoomTool(img, tool_mode='box', drag_buttons='left', always_on=True))
        self.img = img
        self.fix_color_scale(self.data[self.seldata])

        plot.y_axis.title='Altitude [km]'
        plot.title=self.make_plot_title()
        self.update_window_title()
        
        
        plot.underlays.remove(plot.x_axis)
        plot.padding_left = 50
        plot.padding_right = 20
        add_date_axis(plot)
        
        colorbar = chaco.ColorBar(index_mapper=chaco.LinearMapper(range=img.color_mapper.range),
                                    color_mapper=img.color_mapper,
                                    orientation='v',
                                    resizable='v',
                                    width=20,
                                    padding=20)
        colorbar.plot = img
        colorbar.padding_top = plot.padding_top
        colorbar.padding_bottom = plot.padding_bottom
        
        container = chaco.HPlotContainer(plot, colorbar, use_backbuffer=True)
        
        return plot, container
    
    
    def fix_color_scale(self, data_to_show):

        if self.log_scale:
            # reset the color scale minimum
            self.img.color_mapper.range.set_bounds('auto', np.nanmax(data_to_show))
            # be helpful
            self.img.color_mapper.range.set_bounds(self.img.color_mapper.range.low / 2., np.nanmax(data_to_show))
        else:
            # reset the color scale maximum
            self.img.color_mapper.range.set_bounds(np.nanmin(data_to_show), 'auto')
            # be helpful
            self.img.color_mapper.range.set_bounds(np.nanmin(data_to_show), self.img.color_mapper.range.high/2.)
            
        self.cmin, self.cmax = self.img.color_mapper.range.low, self.img.color_mapper.range.high

    
    def _data_type_changed(self):
        
        self.update_data_list()
        self.seldata = self.data_list[0]
        if self.data_type is 'Ratio':
            self.log_scale = False
            
        
    def _seldata_changed(self):
        
        if self.pcolor_data:
            data_to_show = self.data[self.seldata].T.copy()
            
            if self.log_scale:
                # to avoid error message when doing log10(x<0)
                idx_pos = data_to_show > 0
                idx_neg = data_to_show <= 0
                data_to_show[idx_pos] = np.log10(data_to_show[idx_pos])
                data_to_show[idx_neg] = np.nan
            
            self.pcolor_data.set_data('image', data_to_show)
            self.pcolor.title = self.make_plot_title()
            
            self.fix_color_scale(data_to_show)
            
    def _profile_data(self, iprof):
        profile_data = self.data[self.seldata][iprof,:].copy()
        if self.log_scale:
            # little dance to avoid warnings for log10(x<0)
            idx_pos = profile_data > 0
            idx_neg = profile_data <= 0
            profile_data[idx_pos] = np.log10(profile_data[idx_pos])
            profile_data[idx_neg] = np.nan
        return profile_data
        
        
    def _show_profile_fired(self):
        
        if self.profileplot is None:
            profile_data = self._profile_data(0)
            self.profileplot = ProfilePlot(self, profiledata=profile_data, alt=self.alt, profname=0)
            self.profilecontroller = ProfileController(view=self.profileplot)

            # Add line inspector  
            self.line_inspector = self.img.overlays.append(LineInspector(self.img, axis='index_x', inspect_mode='indexed',
                                        write_metadata=True, is_listener=False, is_interactive=True, color='white'))
            self.img.index.on_trait_change(self._metadata_changed, 'metadata_changed')
            self.profileplot.configure_traits(handler=self.profilecontroller)
        
        
    def _reset_zoom_fired(self):
        
        self.pcolor.index_range.set_bounds(*self.epochtime_range)
        self.pcolor.value_range.set_bounds(*self.alt_range)
    
    
    def _scale_more_fired(self):
        if self.log_scale:
            self.cmin /= cmap_change_factor
        else:
            self.cmax *= cmap_change_factor
        self.set_clim()
        
        
    def _scale_less_fired(self):
        if self.log_scale:
            self.cmin *= cmap_change_factor
        else:
            self.cmax /= cmap_change_factor
        self.set_clim()
    
    
    def set_clim(self):
        self.img.color_mapper.range.set_bounds(self.cmin, self.cmax)
        self.img.request_redraw()
        if self.profileplot is not None:
            self.profileplot.profileplot.request_redraw()
    
    
    def _metadata_changed(self, old, new):
        if self.img.index.metadata.has_key('selections'):
            if self.profileplot is not None:
                iprof = self.img.index.metadata['selections'][0]
                profile_data = self._profile_data(iprof)
                self.profileplot.set_profile(profile_data, self.alt, self.datetime[iprof])
    
    
    def _log_scale_changed(self):
        self._seldata_changed()
    
    
    def save_image(self, save_image_file):
        window_size = self.pcolor.outer_bounds
        gc = chaco.PlotGraphicsContext(window_size)
        gc.render_component(self.pcolor)
        gc.save(save_image_file)
        
        
if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        sys.exit('Usage: imageplot.py data_source')
        
    data_source = sys.argv[1]
    imageplot = ImagePlot(data_source=data_source)
    imageplot.configure_traits()
    
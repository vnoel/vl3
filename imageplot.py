#!/usr/bin/env python
# encoding: utf-8
"""
imageplot.py

Created by Vincent Noel on 2011-07-18.
Copyright (c) 2011 LMD/CNRS. All rights reserved.

ImagePlot class for lidar curtain plot.
This script can also be used standalone, as
imageplot.py LNA_FOLDER
"""

import sys
import os
import numpy as np
import chaco.api as chaco
from chaco.tools.api import LineInspector, ZoomTool

from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator

from traits.api import HasTraits, Instance, Button, Bool, Enum, List, Str, Directory, File
from traitsui.api import Item, UItem, View, HGroup, VGroup, Handler
from traitsui.menu import Menu, MenuBar, CloseAction, Action, Separator
from enable.api import ComponentEditor

from pyface.api import MessageDialog

import matplotlib.dates as mdates

import yag
from profile import ProfilePlot

cmap_change_factor = 1.5


def add_date_axis(plot):
    bottom_axis = chaco.PlotAxis(plot, orientation='bottom', tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
    plot.underlays.append(bottom_axis)



class ImagePlot(HasTraits):
    
    data_source = ''
    data_list = List([])
    plot_title = Str('')
    
    data_type = Enum('Backscatter', 'Ratio')
    
    seldata = Enum(values='data_list')
    container = Instance(chaco.HPlotContainer)
    show_profile = Button('Show profile')
    log_scale = Bool
    reset_zoom = Button('Reset Zoom')
    scale_more = Button('Scale++')
    scale_less = Button('Scale--')

    traits_view = View(
        HGroup(
            UItem('data_type'),
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
                Action(name='Open LNA directory...', action='open_dir'),
                Action(name='Open LNA file...', action='open_file'),
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
        title='View Lidar 3',
    )
    
    
    def __init__(self, lna_source=None):
        
        self.pcolor = None
        self.pcolor_data = None
        self.profileplot = None
        # maybe point this to sirta folders
        self.directory_to_load = os.getcwd()
        self.save_image_file = os.getcwd()

        if lna_source:
            self.open_data(lna_source)
        
        
    def open_data(self, lna_source):
        
        if lna_source is None:
            return
            
        print 'Log: opening ', lna_source
        yagdata = yag.open_source(lna_source)

        if yagdata is None:
            msg = MessageDialog(message="No LNA data found in this folder.", severity='warning', title='Problem')
            msg.open()
            return
                
        self.datetime = yagdata['time']
        self.alt = yagdata['alt']
        self.data = yagdata['data']
        self.date = yagdata['date']
        self.data_source = lna_source

        self.alt_range = np.min(self.alt), np.max(self.alt)

        epochtime = mdates.num2epoch(mdates.date2num(self.datetime))
        self.epochtime_range = np.min(epochtime), np.max(epochtime)

        data_type = 'Backscatter'
        self.update_data_list()
        self.seldata = self.data_list[0]

        self.plot_title = str(self.date.date()) + ' [' + self.data_source + ']'
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
        plot.title=self.plot_title
        
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
            self.pcolor.title = '[' + self.data_source + ']: ' + self.seldata
            
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

            # Add line inspector  
            self.line_inspector = self.img.overlays.append(LineInspector(self.img, axis='index_x', inspect_mode='indexed',
                                        write_metadata=True, is_listener=False, is_interactive=True, color='white'))
            self.img.index.on_trait_change(self._metadata_changed, 'metadata_changed')
            self.profileplot.configure_traits()
        
        
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
        sys.exit('Usage: imageplot.py lna_source')
        
    lna_source = sys.argv[1]
    imageplot = ImagePlot(lna_source=lna_source)
    imageplot.configure_traits()
    
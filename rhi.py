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
from traitsui.api import Item, UItem, View, HGroup, VGroup
from traitsui.menu import Menu, MenuBar, CloseAction, Action, Separator
from enable.api import ComponentEditor

from pyface.api import MessageDialog, ImageResource

from lidardata import LidarData, InvalidFormat
from profile import ProfilePlot, ProfileController

from config import minor_version, major_version
from config import basesirta_path

# change factor for colormap caxis
cmap_change_factor = 2.

menubar=MenuBar(
    Menu(
        CloseAction,
        Separator(),
        Action(name='&New window', action='new_empty_view', accelerator='Ctrl+N'),
        Action(name='&Open data file...', action='open_file', accelerator='Ctrl+O'),
        Action(name='Open data directory...', action='open_dir', accelerator='Shift+Ctrl+O'),
        '_',
        Action(name='&Save Plot...', action='save', accelerator='Ctrl+S', enabled_when='plot_title !=""'),
        # Action(name='Quit', action='quit', accelerator='Ctrl+Q'),
        name='&File',
    ),
    Menu(
        Action(name='New view', action='new_view', enabled_when='plot_title != ""'),
        name='View',
    ),
    Menu(
        Action(name='About', action='about_dialog'),
        name='Help'
    ),
)


def add_date_axis(plot):
    bottom_axis = chaco.PlotAxis(plot, orientation='bottom', tick_generator=ScalesTickGenerator(scale=CalendarScaleSystem()))
    plot.underlays.append(bottom_axis)


class Rhi(HasTraits):
    
    data_list = List([])
    data_source = None
    profileplot = None
    plot_title = Str('')
    window_title = Str('View Lidar 3 v%d.%d' % (major_version, minor_version))
    
    icon_img = ImageResource('icon', search_path=[os.getcwd()+'/', './', '/users/noel/vl3/', sys.path[0]])
    
    data_type = Enum('Signal', 'Ratio')
    seldata = Enum(values='data_list')
    container = Instance(chaco.HPlotContainer)
    show_profile = Button('Show profile')
    log_scale = Bool
    reset_zoom = Button('Reset Zoom')
    scale_more = Button('Scale++')
    scale_less = Button('Scale--')
    
    open_file_button = Button('Open File...')
    open_folder_button = Button('Open Folder...')

    traits_view = View(
        # this bit of the view is only visible when there's no data
        # ie at startup and empty views
        HGroup(
            UItem('open_file_button', padding=15, springy=True),
            UItem('open_folder_button', padding=15, springy=True),
            springy=True,
            visible_when='plot_title == ""'
        ),
        # this bit of the view shows when there is data
        # ie after file/folder loading
        VGroup(
            HGroup(
                UItem('data_type', visible_when='lidardata.has_ratio is True'),
                UItem('seldata', springy=True),
            ),
            UItem('container', editor=ComponentEditor(), width=800, height=300),
            HGroup(
                UItem('show_profile'),
                UItem('reset_zoom'),
                UItem('scale_less'),
                UItem('scale_more'),
                Item('log_scale', label='Log Scale', visible_when='"Signal" in data_type'),
            ),
            visible_when='plot_title != ""'
        ),
        menubar=menubar,
        resizable=True,
        title=str(window_title),
        icon=icon_img
    )
    
    
    def __init__(self, data_source=None, base_folder=basesirta_path):
                
        self.pcolor_data = chaco.ArrayPlotData()
        self.pcolor_data.set_data('image', np.zeros([1,1]))
        self.pcolor, self.container, self.colorbar = self.pcolor_create(self.pcolor_data)

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
                

    def _open_file_button_fired(self):
        self.handler.open_file(None)
        
        
    def _open_folder_button_fired(self):
        self.handler.open_dir(None)
        
        
    def open_data(self, data_source):
        
        if data_source is None:
            return
            
        try:
            lidardata = LidarData(from_source=data_source)
        except InvalidFormat as inst:
            msg = MessageDialog(message=inst.args[0], severity='warning', title='Problem')
            msg.open()
            return
            
        self.data_source = data_source
        self.lidardata = lidardata
                
        self.data_type = 'Signal'
        self.update_data_list(self.data_type)
        self.seldata = self.data_list[0]

        self.pcolor_set_data(self.lidardata.data[self.seldata].T)
        
                
        
    def update_data_list(self, data_type):
        
        data_list = []
        for key in self.lidardata.data.keys():
            if 'Ratio' in key:
                if data_type is 'Ratio':
                    data_list.append(key)
            else:
                if data_type is not 'Ratio':
                    data_list.append(key)
                    
        data_list.sort()
        self.data_list = data_list
        
        
    def update_titles(self):
        if self.data_source is None:
            return
            
        self.window_title = 'View Lidar 3 v%d.%d' % (major_version, minor_version) + ' - ' + str(self.lidardata.date.date())
        self.plot_title = str(self.lidardata.date.date()) + ' : ' + self.seldata
        self.pcolor.title = self.plot_title
        # colorbar titles
        ctitle = self.seldata
        if self.log_scale:
            ctitle = ctitle + ' [Log10]'
        self.colorbar._axis.title = ctitle

        
    def set_plot_boundaries(self):
        datasource = self.pcolor.range2d.sources[0]
        datasource.set_data(self.lidardata.epochtime, self.lidardata.alt)
        
        
    def set_color_scale(self, data_to_show):

        min = np.nanmin(data_to_show)
        max = np.nanmax(data_to_show)
        range = max-min

        if not self.log_scale:
            datarange = [min, max - range*0.25]
        else:
            datarange = [min + range*0.25, max]

        self.img.color_mapper.range.set_bounds(datarange[0], datarange[1])            
        self.cmin, self.cmax = self.img.color_mapper.range.low, self.img.color_mapper.range.high


    def pcolor_set_data(self, array_data):
        
        self.pcolor_data.set_data('image', array_data)
        self.set_color_scale(array_data)
        self.set_plot_boundaries()
        
        self.update_titles()
        
        
    def pcolor_create(self, pcolor_data):
                        
        plot = chaco.Plot(self.pcolor_data, padding=40)

        # DON'T FORGET THE [0] to get a handle to the actual plot
        self.img = plot.img_plot('image', 
                                colormap=chaco.jet, xbounds=(0,1.), ybounds=(0,1.),
                                padding_left=40, 
                                padding_right=30)[0]
        self.img.overlays.append(ZoomTool(self.img, tool_mode='box', drag_buttons='left', always_on=True))

        plot.y_axis.title='Range [km]'
        plot.underlays.remove(plot.x_axis)
        add_date_axis(plot)
        
        # left padding must be at least 50 to accomodate changes in number label width
        colorbar = chaco.ColorBar(index_mapper=chaco.LinearMapper(range=self.img.color_mapper.range),
                                    color_mapper=self.img.color_mapper,
                                    plot=self.img,
                                    orientation='v',
                                    resizable='v',
                                    width=20,
                                    padding=20,
                                    padding_left=50,
                                    padding_top=plot.padding_top,
                                    padding_bottom=plot.padding_bottom)

        container = chaco.HPlotContainer(colorbar, plot, use_backbuffer=True)
        
        return plot, container, colorbar
    
    
    def _data_type_changed(self):
        
        self.update_data_list(self.data_type)
        self.seldata = self.data_list[0]
        if self.data_type is 'Ratio':
            self.log_scale = False
        
        
    def _seldata_changed(self):
        
        if self.pcolor_data is None:
            return 

        if self.data_type is 'Ratio':
            self.log_scale = False
            
        data_to_show = self.lidardata.data[self.seldata].T.copy()
        
        if self.log_scale:
            # to avoid error message when doing log10(x<0)
            idx_pos = data_to_show > 0
            idx_neg = data_to_show <= 0
            data_to_show[idx_pos] = np.log10(data_to_show[idx_pos])
            data_to_show[idx_neg] = np.nan
            
        self.pcolor_set_data(data_to_show)
        
        
    def _profile_data(self, iprof):
        profile_data = self.lidardata.data[self.seldata][iprof,:].copy()
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
            self.profileplot = ProfilePlot(self, profiledata=profile_data, alt=self.lidardata.alt, profname=0)
            self.profilecontroller = ProfileController(view=self.profileplot)

            # Add line inspector  
            self.line_inspector = self.img.overlays.append(LineInspector(self.img, axis='index_x', inspect_mode='indexed',
                                        write_metadata=True, is_listener=False, is_interactive=True, color='white'))
            self.img.index.on_trait_change(self._metadata_changed, 'metadata_changed')
            self.profileplot.configure_traits(handler=self.profilecontroller)
        
        
    def _reset_zoom_fired(self):
        
        self.pcolor.index_range.set_bounds(*self.lidardata.epochtime_range)
        self.pcolor.value_range.set_bounds(*self.lidardata.alt_range)
    
    
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
                self.profileplot.set_profile(profile_data, self.lidardata.alt, self.lidardata.datetime[iprof])
    
    
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
    rhi = Rhi(data_source=data_source)
    rhi.configure_traits()
    
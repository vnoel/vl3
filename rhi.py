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
from chaco.tools.api import LineInspector, ZoomTool, PanTool
# from chaco.tools.api import RangeSelection, RangeSelectionOverlay

# the regular ZoomTool does not work in colorbars
from chaco.tools.simple_zoom import SimpleZoom as CZoomTool

from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator

from traits.api import HasTraits, Instance, Button, Bool, Enum, List, Str
from traitsui.api import Item, UItem, View, HGroup, VGroup, Label
from traitsui.menu import Menu, MenuBar, CloseAction, Action, Separator
from enable.api import ComponentEditor

from pyface.api import MessageDialog, ImageResource

from lidardata import LidarData, InvalidFormat
from profile import ProfilePlot, ProfileController

from config import minor_version, major_version
from config import basesirta_path

from dialogs import AxisRange, ColorScaleRange
from util import signal_ratio


# change factor for colormap caxis
cmap_change_factor = 1.5

menubar = MenuBar(
    Menu(
        CloseAction,
        Separator(),
        Action(name='&New window', action='new_empty_view', accelerator='Ctrl+N'),
        Action(name='&Open data file...', action='open_file', accelerator='Ctrl+O'),
        Action(name='Open data directory...', action='open_dir', accelerator='Shift+Ctrl+O'),
        '_',
        Action(name='&Save Plot...', action='save', accelerator='Ctrl+S', enabled_when='plot_title !=""'),
        Action(name='Save Profile Plot...', action='save_profile', enabled_when='p rofileplot is not None'),
        # Action(name='Quit', action='quit', accelerator='Ctrl+Q'),
        name='&File',
    ),
    Menu(
        Action(name='New view', action='new_view', enabled_when='plot_title != ""'),
        Separator(),
        Action(name='Adjust axis...', action='adjust_axis'),
        Action(name='Adjust color scale...', action='adjust_color_scale'),
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
    denum_seldata = Enum(values='data_list')
    
    container = Instance(chaco.HPlotContainer)
    show_profile = Button('Show profile')
    log_scale = Bool
    range_correct = Bool
    reset_zoom = Button('Reset Zoom')
    scale_more = Button('Scale++')
    scale_less = Button('Scale--')
    adjust_axis = Button('Adjust Axis')
    
    # if "binary", special-case for old binary lna
    filetype = Str('')
    
    open_file_button = Button('Open File...')
    open_folder_button = Button('Open Folder...')

    traits_view = View(
        # this bit of the view is only visible when there's no data
        # ie at startup and empty views
        VGroup(
            HGroup(
            UItem('open_file_button', padding=15, springy=True),
            UItem('open_folder_button', padding=15, springy=True),
            ),
            springy=True,
            visible_when='plot_title == ""'
        ),
        
        # this bit of the view shows when data is opened
        # ie after file/folder loading
        
        VGroup(
            HGroup(
                UItem('data_type', visible_when='len(seldata) > 1'),
                UItem('seldata', springy=True),
                Item('denum_seldata', springy=True, visible_when='data_type=="Ratio"', label='/ ')
            ),
            UItem('container', editor=ComponentEditor(size=(800, 400))),
            HGroup(
                UItem('show_profile'),
                UItem('adjust_axis'),
                UItem('reset_zoom'),
                UItem('scale_less'),
                UItem('scale_more'),
                Item('log_scale', label='Log Scale', visible_when='"Signal" in data_type'),
                Item('range_correct', label='range-correct data', visible_when='"binary" in filetype and data_type!="Ratio"')
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

        self.save_image_file = os.getcwd() + '/figure.png'
        self.save_profile_file = os.getcwd() + '/profile.png'

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
                

    def _adjust_axis_fired(self):
        '''
        opens a dialog to select the vertical axis boundaries
        '''
        
        axisrange = AxisRange(*self.lidardata.alt_range)
        axisrange.configure_traits(kind='modal')
        # here the user clicked on ok
        ymin, ymax = axisrange.range()
        ymin = np.max([self.lidardata.alt_range[0], ymin])
        ymax = np.min([self.lidardata.alt_range[1], ymax])        
        self.pcolor.value_range.set_bounds(ymin, ymax)
        
        
    def _adjust_color_scale_fired(self):
        
        crange = [self.img.color_mapper.range.low, self.img.color_mapper.range.high]
        colorscale = ColorScaleRange(*crange)
        colorscale.configure_traits(kind='modal')
        ymin, ymax = colorscale.range()
        self.img.color_mapper.range.set_bounds(ymin, ymax)


    def _open_file_button_fired(self):
        self.handler.open_file(None)
        
        
    def _open_folder_button_fired(self):
        self.handler.open_dir(None)
        
        
    def open_data(self, data_source):
        
        if data_source is None:
            return
            
        try:
            self.lidardata = LidarData(from_source=data_source)
        except InvalidFormat as inst:
            msg = MessageDialog(message=inst.args[0], severity='warning', title='Problem')
            msg.open()
            return
            
        self.data_source = data_source
                
        self.data_type = 'Signal'
        
        # get file type (netcdf or binary)
        self.filetype = self.lidardata.filetype
        if self.filetype != 'binary':
            self.range_correct = False
            
        self.update_data_list(self.data_type)
        self.seldata = self.data_list[0]
        self.directory_to_load = data_source

        self.pcolor_set_data(self.lidardata.data[self.seldata].T)
        
    def update_data_list(self, data_type):
        
        data_list = self.lidardata.data.keys()
        data_list.sort()
        self.data_list = data_list
        
        
    def update_titles(self):
        '''
        Update all the titles - window, plot, colorbar
        '''
        
        if self.data_source is None:
            return
            
        self.window_title = 'View Lidar 3 v%d.%d' % (major_version, minor_version) + ' - ' + str(self.lidardata.date.date())
        if self.data_type=='Ratio':
            self.plot_title = str(self.lidardata.date.date()) + ' : Ratio ' + self.seldata + '/' + self.denum_seldata
        else:
            self.plot_title = str(self.lidardata.date.date()) + ' : ' + self.seldata
            
        self.pcolor.title = self.plot_title
        self.window_title = 'View Lidar 3 v%d.%3.1f' % (major_version, minor_version) + ' - ' + self.plot_title
        
        # colorbar title
        self.colorbar._axis.title = self.seldata+' [Log10]' if self.log_scale else self.seldata

        
    def set_plot_boundaries(self):
        '''
        sets the range for the vertical and horizontal axis
        this method to set the axis range of an img_plot after its creation comes from
        http://markmail.org/message/r5m2dmkff3kvotek#query:+page:1+mid:zf6u7xtntjvsdpnq+state:results
        '''
        
        datasource = self.pcolor.range2d.sources[0]
        datasource.set_data(self.lidardata.epochtime, self.lidardata.alt)
        
        self.img.x_mapper.domain_limits = (self.lidardata.epochtime[0], self.lidardata.epochtime[-1])
        self.img.y_mapper.domain_limits = (self.lidardata.alt[0], self.lidardata.alt[-1])


    def set_color_scale(self, data_to_show):
        '''
        sets the range for the plot color scale, using the min and max value of the displayed data array.
        '''

        min = np.nanmin(data_to_show)
        max = np.nanmax(data_to_show)
        range = max - min

        if not self.log_scale:
            datarange = [min, max - range*0.25]
        else:
            datarange = [min + range*0.25, max]

        self.img.color_mapper.range.set_bounds(datarange[0], datarange[1])
        self.colorbar.index_mapper.domain_limits = (datarange[0], datarange[1])
        
        self.cmin, self.cmax = self.img.color_mapper.range.low, self.img.color_mapper.range.high


    def pcolor_set_data(self, array_data):
        '''
        sets the data displayed in the plot.
        fixes the color scale and plot ranges accordingly.
        updates the plot title accordingly.
        '''
        
        self.pcolor_data.set_data('image', array_data)
        self.set_color_scale(array_data)
        self.set_plot_boundaries()
        
        self.update_titles()
        
        
    def pcolor_create(self, pcolor_data):
        '''
        Creates the plot object and fills it with initial data
        '''
                        
        plot = chaco.Plot(self.pcolor_data, padding=40)

        # DON'T FORGET THE [0] to get a handle to the actual plot
        self.img = plot.img_plot('image', 
                                colormap=chaco.jet, xbounds=(0,1.), ybounds=(0,1.),
                                padding_left=40, 
                                padding_right=30)[0]
        self.img.overlays.append(ZoomTool(self.img, tool_mode='box', drag_buttons='left', always_on=True))
        self.img.tools.append(PanTool(self.img, always_on=True, drag_button='right'))

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
        
        # range selection in the colorbar
        # not extremely useful

        # range_selection = RangeSelection(component=colorbar)
        # colorbar.tools.append(range_selection)
        # colorbar.overlays.append(RangeSelectionOverlay(colorbar, border_color='white', alpha=0.8, fill_color='white'))
        # range_selection.listeners.append(self.img)
        
        colorbar.tools.append(PanTool(colorbar, constrain_direction='y', constrain=True, drag_button='right'))

        # make the colorbar zoomable
        # cannot use ZoomTool, as it tries to access the x_mapper and y_mapper of the zoomed component (here colorbar)
        # and colorbar only has y_mapper (x_mapper is None), which leads to an exception in _map_coordinate_box        
        
        zoom_overlay = CZoomTool(component=colorbar, axis='index', tool_mode='range', always_on=True, drag_button='left')
        colorbar.overlays.append(zoom_overlay)

        container = chaco.HPlotContainer(colorbar, plot, use_backbuffer=True)
        
        return plot, container, colorbar
    
    
    def _data_type_changed(self):
        
        self.update_data_list(self.data_type)
        if self.data_type is 'Ratio':
            self.seldata = self.data_list[1]
            self.denum_seldata = self.data_list[0]
            self.log_scale = False
        else:
            self.seldata = self.data_list[0]
        
        
    def _denum_seldata_changed(self):
        
        self._seldata_changed()
        
        
    def _seldata_changed(self):
        
        if self.pcolor_data is None:
            return 
            
        if self.data_type is 'Ratio':
            print 'Data is ratio ', self.seldata, '/', self.denum_seldata
            data_to_show = signal_ratio(self.lidardata.data[self.denum_seldata], self.lidardata.data[self.seldata]).T
            self.log_scale = False
            self.range_correct = False
        else:
            data_to_show = self.lidardata.data[self.seldata].T.copy()
        
        if self.range_correct:
            r2 = np.power(self.lidardata.alt, 2)
            for i in np.r_[0:data_to_show.shape[1]]:
                data_to_show[:,i] = data_to_show[:,i] * r2
        
        if self.log_scale:
            # to avoid error message when doing log10(x<0)
            idx_pos = data_to_show > 0
            idx_neg = data_to_show <= 0
            data_to_show[idx_pos] = np.log10(data_to_show[idx_pos])
            data_to_show[idx_neg] = np.nan
                        
        self.pcolor_set_data(data_to_show)
        
        
    def _profile_data(self, iprof):

        profile_data = self.lidardata.data[self.seldata][iprof,:].copy()

        if self.range_correct:
            r2 = np.power(self.lidardata.alt, 2)
            profile_data *= r2            
            
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
        
        
    def _metadata_changed(self, old, new):
        if self.img.index.metadata.has_key('selections'):
            if self.profileplot is not None:
                iprof = self.img.index.metadata['selections'][0]
                if iprof is not None:
                    profile_data = self._profile_data(iprof)
                    self.profileplot.set_profile(profile_data, self.lidardata.alt, str(self.lidardata.datetime[iprof]))


    def _reset_scale_fired(self):
        
        self.img.color_mapper.range.set_bounds(self.cmin, self.cmax)            
        
        
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
        
    
    def _log_scale_changed(self):
        self._seldata_changed()
        
    def _range_correct_changed(self):
        self._seldata_changed()
    
    
    def save_image(self, save_image_file):
        window_size = self.container.outer_bounds
        print window_size
        gc = chaco.PlotGraphicsContext([window_size[0]+1, window_size[1]+1])
        gc.render_component(self.container)
        gc.save(save_image_file)
        
        
if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        sys.exit('Usage: imageplot.py data_source')
        
    data_source = sys.argv[1]
    rhi = Rhi(data_source=data_source)
    rhi.configure_traits()
    
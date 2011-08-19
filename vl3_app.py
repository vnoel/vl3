#!/usr/bin/env python
# encoding: utf-8
"""
vl3_app.py

Created by Vincent Noel on 2011-07-18.
Copyright (c) 2011 LMD/CNRS. All rights reserved.

This is the main program for the vl3 application.
Takes care of creating menus and stuff.
"""

import sys, os

from pyface.api import FileDialog, DirectoryDialog, AboutDialog, OK, ImageResource
from traits.api import Instance
from traitsui.api import Handler

from imageplot import ImagePlot


class ImagePlotController(Handler):
    
    view = Instance(ImagePlot)

    def init(self, info):
        # reference to the imageplot object view
        self.view = info.object


    def open_source(self, source_type):
        print 'Log: Select ', source_type
        dlg = DirectoryDialog if source_type=='directory' else FileDialog
        fd = dlg(action='open', default_path=self.view.directory_to_load)
        if fd.open() == OK:
            print 'Opening ', fd.path
            self.view.open_data(fd.path)
        

    def open_dir(self, ui_info):
        self.open_source('directory')
                
                
    def open_file(self, ui_info):
        self.open_source('file')
        
        
    def save(self, ui_info):
        print 'Log: Saving image'
        fd = FileDialog(action='save as', default_path=self.view.save_image_file)
        if fd.open() == OK:
            print 'saving to ', fd.path
            self.view.save_image(fd.path)
            
        
    def new_empty_view(self, ui_info):
        print 'Log: New empty view'
        image = ImagePlot()
        controller = ImagePlotController(view=image)
        image.configure_traits(handler=controller)

        
    def new_view(self, ui_info):
        print 'Log: New view'
        image = ImagePlot(lna_source=self.view.data_source)
        controller = ImagePlotController(view=image)
        image.configure_traits(handler=controller)

    
    def about_dialog(self, ui_info):
        
        img = ImageResource('about', search_path=[os.getcwd()+'/', './'])
        text=['VL3 - View Lidar 3 - v0.1\n', u'© VNoel 2001-2011 - LMD/CNRS/IPSL\n', 
            'Based on input and help from M. Chiriaco, A. Delaval, Y. Morille, S. Turquety.',
            'Using the Enthought Tool Suite (ETS), Python.']
        dlg = AboutDialog(parent=ui_info.ui.control, additions=text, image=img)
        dlg.open()
        
        
    def close(self, info, is_ok):
        print 'Log: Closing'
        # would be nice to close the profile plot
        # but easier said than done
        # tip: info.ui.dispose()
        return Handler.close(self, info, is_ok)
    
        
if __name__ == '__main__':
    
    if len(sys.argv) > 1:
        yagfile = sys.argv[1]
    else:
        yagfile = None
    
    imageapp = ImagePlot(yagfile)
    controller = ImagePlotController(view=imageapp)
    imageapp.configure_traits(handler=controller)
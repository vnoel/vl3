#!/usr/bin/env python
# encoding: utf-8
"""
controller.py

Created by Vincent Noel - LMD/CNRS on 2011-11-22.
"""

import sys, os

from pyface.api import FileDialog, DirectoryDialog, AboutDialog, OK, ImageResource
from traits.api import Instance
from traitsui.api import Handler

from rhi import Rhi
from config import minor_version, major_version


class RhiController(Handler):
    
    view = Instance(Rhi)

    def init(self, info):
        # reference to the rhi object view
        self.view = info.object
        self.view.handler = self


    def quit(self, ui_info):
        sys.exit(0)
        # ui_info.ui.dispose()
        

    def open_source(self, source_type):
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
        fd = FileDialog(action='save as', default_path=self.view.save_image_file)
        if fd.open() == OK:
            print 'saving to ', fd.path
            self.view.save_image(fd.path)
            
        
    def new_empty_view(self, ui_info):
        
        rhi = Rhi()
        controller = RhiController(view=rhi)
        rhi.configure_traits(handler=controller)

        
    def new_view(self, ui_info):
        
        if self.view.data_source:
            rhi = Rhi(data_source=self.view.data_source)
        else:
            # this should not happen...
            rhi = Rhi()
            
        controller = RhiController(view=rhi)
        rhi.configure_traits(handler=controller)
        
    def adjust_axis(self, ui_info):
        self.view._adjust_axis_fired()
        
    def adjust_color_scale(self, ui_info):
        self.view._adjust_color_scale_fired()

    
    def about_dialog(self, ui_info):
        img = ImageResource('about', search_path=[os.getcwd()+'/', './', '/users/noel/vl3/'])
        text=['VL3 - View Lidar 3 - v%d.%d\n' % (major_version, minor_version), 
            u'© VNoel 2001-2011 - LMD/CNRS/IPSL\n', 
            'Based on input and help from M. Chiriaco, A. Delaval, Y. Morille, C. Pietras, S. Turquety.',
            'Using the Enthought Tool Suite (ETS), Python.']
        dlg = AboutDialog(parent=ui_info.ui.control, additions=text, image=img)
        dlg.open()
        
        
    def object_window_title_changed(self, info):
        info.ui.title = self.view.window_title
        
        
    def close(self, info, is_ok):
        # would be nice to close the profile plot
        # but easier said than done
        # tip: info.ui.dispose()
        return Handler.close(self, info, is_ok)

def main():
    pass


if __name__ == '__main__':
    main()


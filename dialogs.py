#!/usr/bin/env python
# encoding: utf-8
"""
dialogs.py

Created by Vincent Noel - LMD/CNRS on 2012-02-10.
"""

from traits.api import HasTraits, Float
from traitsui.api import Item, View
from traitsui.menu import OKCancelButtons


class _TwoValuesSelectorDialog(HasTraits):
    
    ymin = Float()
    ymax = Float()
    view = View(Item('ymin'), Item('ymax'), buttons=OKCancelButtons, title='Adjust Values')
    
    def __init__(self, ymin, ymax):
        self.ymin = ymin
        self.ymax = ymax

    def range(self):
        return self.ymin, self.ymax
    

class AxisRange(_TwoValuesSelectorDialog):
    
    ymin = Float(label='Min altitude [km]')
    ymax = Float(label='Max altitude [km]')
        

class ColorScaleRange(_TwoValuesSelectorDialog):
    
    ymin = Float(label='Min value')
    ymax = Float(label='Max value')


def main():
    pass


if __name__ == '__main__':
    main()


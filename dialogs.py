#!/usr/bin/env python
# encoding: utf-8
"""
dialogs.py

Created by Vincent Noel - LMD/CNRS on 2012-02-10.
"""

from traits.api import HasTraits, Float
from traitsui.api import Item, View
from traitsui.menu import OKCancelButtons

class AxisRange(HasTraits):
    
    ymin = Float(0, label='Min altitude [km]')
    ymax = Float(15, label='Max altitude [km]')
    view = View(Item('ymin'), Item('ymax'), buttons=OKCancelButtons)

    def __init__(self, ymin, ymax):
        self.ymin = ymin
        self.ymax = ymax

    def range(self):
        return self.ymin, self.ymax
    


def main():
    pass


if __name__ == '__main__':
    main()


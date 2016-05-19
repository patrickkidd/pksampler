"""
A knob. Should this be a wheel instead?
"""
from PyQt4.QtCore import SIGNAL
from pixmapwidgets import CyclicSlider


class Knob(CyclicSlider):
    def __init__(self, parent=None, name='knob'):
        CyclicSlider.__init__(self, parent, 'knob', 0, 20)
        

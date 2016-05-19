"""
Implemenation of 'mixerslider' povray widget.
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QSlider
from pixmapwidgets import PixmapSlider


class MixerSlider(PixmapSlider):
    def __init__(self, parent=None):
        PixmapSlider.__init__(self, parent, 'mixerslider', 0, 127,
                              Qt.Vertical)
        self.setRange(0, 127)
        self.setSingleStep(1)
        self.setPageStep(5)
        self.setValue(0)


"""
Implemenation of 'mixerslider' povray widget.
A somewhat standard pixmap button with an LCD label.
"""

from PyQt4.QtCore import QTimer, QObject, QPoint, SIGNAL
from PyQt4.QtGui import QPainter, QColor, QPalette
from pixmapwidgets import PixmapButton


class Button(PixmapButton):
    def __init__(self, parent=None, name='button', color='gray'):
        PixmapButton.__init__(self, name,
                              min=0, max=17,
                              color=color, parent=parent)


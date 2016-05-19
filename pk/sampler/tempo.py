#   Copyright (C) 2006 by Patrick Stinson                                 
#   patrickkidd@gmail.com                                                   
#                                                                         
#   This program is free software; you can redistribute it and/or modify  
#   it under the terms of the GNU General Public License as published by  
#   the Free Software Foundation; either version 2 of the License, or     
#   (at your option) any later version.                                   
#                                                                         
#   This program is distributed in the hope that it will be useful,       
#   but WITHOUT ANY WARRANTY; without even the implied warranty of        
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         
#   GNU General Public License for more details.                          
#                                                                         
#   You should have received a copy of the GNU General Public License     
#   along with this program; if not, write to the                         
#   Free Software Foundation, Inc.,                                       
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.  
#
"""
Beat Matching equipment.
"""

from PyQt4.QtCore import SIGNAL, Qt, QObject, QTimer
from PyQt4.QtGui import QWidget, QColor, QPainter, QVBoxLayout, QLabel, QPalette
from pk.widgets import pixmapwidgets


class Adjuster(QWidget):
    """ 2D Adjuster """
    
    threshhold = 6
    accel_brush = QColor('red')
    diff_brush = QColor('blue')

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self._last_y = None
        self._last_x = None
        self._diff = None
    
    def paintEvent(self, e):
        painter = QPainter(self)
        if self._diff is None:
            color = QColor(self.diff_brush)
            color.setAlpha(25)
        else:
            color = self.diff_brush
            a = abs(self._diff) * 1.7
            if a > 75: a == 75
            color.setAlpha(25 + a)
        painter.setPen(color)
        painter.setBrush(color)
        painter.drawRect(e.rect())

    def mousePressEvent(self, e):
        self._last_x = e.x()
        self._last_y = e.y()

    def mouseMoveEvent(self, e):
        x_diff = 0
        y_diff = 0
        if e.x() != self._last_x:
            x_diff = e.x() - self._last_x
            x_diff *= 4
            self._last_x = e.x()
            self.emit(SIGNAL('moved_x(int)'), x_diff)
        if e.y() != self._last_y:
            y_diff = e.y() - self._last_y
            self._last_y = e.y()
            self.emit(SIGNAL('moved_y(int)'), y_diff)
        self._diff = x_diff + y_diff / 2
        self.update()

    def mouseReleaseEvent(self, e):
        self._last_y = None
        self._last_x = None
        self._diff = None
        self.update()
        self.emit(SIGNAL('released'))


class TempoAdjuster(QWidget):

    tempo = 140.0
    factor = 75.0
    format = '%0.3fbpm'
    slide_factor = 100.0
    slide_interval = 25
    slide_step = .15
    
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        Layout = QVBoxLayout(self)
        Layout.setMargin(0)
        Layout.setSpacing(5)

        self._block_emit = False
        
        self.actualLabel = QLabel(self)
        self.actualLabel.setFixedHeight(25)
        font = self.actualLabel.font()
        font.setPointSize(20)
        self.actualLabel.setFont(font)
        self.actualLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        Layout.addWidget(self.actualLabel)

        self.slideLabel = QLabel(self)
        self.slideLabel.setFixedHeight(25)
        font = self.slideLabel.font()
        font.setPointSize(20)
        self.slideLabel.setFont(font)
        self.slideLabel.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        Layout.addWidget(self.slideLabel)
        
        self.adjuster = Adjuster(self)
        base = QColor(Adjuster.diff_brush)
        base.setAlpha(100)
        self.adjuster.palette().setColor(QPalette.Window, base)
        Layout.addWidget(self.adjuster)

        QObject.connect(self.adjuster, SIGNAL('moved_x(int)'),
                        self.adjust)
        QObject.connect(self.adjuster, SIGNAL('moved_y(int)'),
                        self.set_slide_tempo)
        QObject.connect(self.adjuster, SIGNAL('released'),
                        self.start_slide)

        self._slide_tempo = self.tempo
        self._slide_timer = QTimer(self)
        QObject.connect(self._slide_timer, SIGNAL('timeout()'),
                        self.do_slide)
        self.adjust(0.0)

    def set_slide_tempo(self, delta):
        delta *= -1
        self._slide_tempo += delta / self.slide_factor
        self.slideLabel.setText(self.format % self._slide_tempo)
        self.emit(SIGNAL('tempo(float)'), self._slide_tempo)

    def start_slide(self):
        if self._slide_tempo != self.tempo:
            if self._slide_timer.isActive():
                self._slide_timer.stop()
            self.do_slide()
            self._slide_timer.start(self.slide_interval)
            self.emit(SIGNAL('tempo(float)'), self._slide_tempo)

    def do_slide(self):
        if self._slide_tempo > self.tempo:
            self._slide_tempo -= self.slide_step
            if self._slide_tempo < self.tempo:
                self._slide_tempo = self.tempo
        elif self._slide_tempo < self.tempo:
            self._slide_tempo += self.slide_step
            if self._slide_tempo > self.tempo:
                self._slide_tempo = self.tempo
        self.slideLabel.setText(self.format % self._slide_tempo)
        self.emit(SIGNAL('tempo(float)'), self._slide_tempo)
        if self._slide_tempo == self.tempo:
            self._slide_timer.stop()

    def set_tempo(self, tempo, emit=True):
        self.tempo = tempo
        self._block_emit = True
        self.adjust(0.0)
        self._block_emit = False

    def adjust(self, delta):
        self.tempo += delta / self.factor
        self._slide_tempo = self.tempo
        self.actualLabel.setText(self.format % self.tempo)
        self.slideLabel.setText(self.format % self._slide_tempo)
        if self._block_emit is False:
            self.emit(SIGNAL('tempo(float)'), self.tempo)


if __name__ == '__main__':
    from PyQt4.QtGui import QApplication
    app = QApplication([])
    adjuster = TempoAdjuster()
    adjuster.resize(200, 500)
    adjuster.show()
    app.exec_()

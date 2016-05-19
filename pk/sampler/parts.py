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
Musical parts
"""
import random
from PyQt4.QtCore import Qt, QObject, SIGNAL, QMimeData, QPoint, QString
from PyQt4.QtCore import QRect, QRectF
from PyQt4.QtGui import QApplication, QFrame, QDrag, QPalette, QColor
from PyQt4.QtGui import QPainter, QPixmap
import pk.widgets
import spec


class Part(QFrame):

    margin = 3
    data = None
    text = None
    selected = False
    
    def __init__(self, data, parent=None, draggable=True):
        QFrame.__init__(self, parent)
        self.setFixedSize(spec.PART_WIDTH, spec.PART_HEIGHT)
        self.data = data
        self.drag_start = None
        self.draggable = draggable
        self._base = None
        self.base_color(QColor('grey'))

    def mousePressEvent(self, e):
        self.drag_start = e.pos()

    def mouseMoveEvent(self, e):
        if self.drag_start is None:
            pass
        x = e.x() - self.drag_start.x()
        y = e.y() - self.drag_start.y()
        dist = QApplication.startDragDistance()
        if not self.draggable or x > dist or y > dist:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.__class__.__name__)
        mime.part = self
        drag.setMimeData(mime)
        pixmap = QPixmap.grabWidget(self)
        pixmap.setAlphaChannel(pixmap)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(drag.pixmap().width() / 2,
                               drag.pixmap().height()))
        drag.start(Qt.CopyAction)
    
    def mouseReleaseEvent(self, e):
        x = e.x() - self.drag_start.x()
        y = e.y() - self.drag_start.y()
        dist = QApplication.startDragDistance()
        if x < dist and y < dist:
            self.emit(SIGNAL('selected(QWidget *)'), self)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setBrush(self._base)
        if self.selected:
            painter.pen().setColor(QColor('yellow'))
        else:
            painter.pen().setColor(self._base.dark(150))
        painter.pen().setWidth(self.margin)
        painter.drawRect(0, 0, self.width(), self.height())

    def drawText(self, text=None):
        painter = QPainter(self)
        color = painter.pen().color()
        color.setAlpha(215)
        painter.setPen(color)

        if text is None:
            if self.text:
                text = self.text
            elif self.data:
                text = str(self.data.name)
            else:
                text = str(self.data)

        rect = QRect(5, 0, self.width(), self.height())
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignBottom, QString(text))

    def set_selected(self, on):
        self.selected = on
        self.update()

    def copy(self):
        if self.data:
            newdata = self.data.copy()
        else:
            newdata = None
        newone = self.__class__(newdata)
        newone.text = self.text
        return newone

    def base_color(self, color):
        self._base = color.light(135)

    def active_color(self, color):
        self._active = color.light(135)

    def setData(self, data):
        self.data = data
        self.update()


class SynthPart(Part):

    pattern = None
    stream = None
    
    def __init__(self, synth, parent=None):
        Part.__init__(self, synth, parent)
        self.setAutoFillBackground(True)
        self.base_color(QColor('green'))
        self.pattern = None
        self._SYNTH_POINTS = []
        for x in range(self.margin+1, spec.PART_WIDTH - self.margin, 3):
            y = random.randint(10, spec.PART_HEIGHT - 10)
            self._SYNTH_POINTS.append(QPoint(x, y))
        self.activeLED = pk.widgets.LED(self)
        self.activeLED.setFixedSize(15, 7)
        self.activeLED.setAutoFillBackground(True)
        self.activeLED.palette().setColor(self.activeLED.backgroundRole(),
                                          QColor('grey').dark(110))
        self.activeLED.move(self.width() - self.activeLED.width() - 5, 5)
        self.activeLED.hide()

    def paintEvent(self, e):
        Part.paintEvent(self, e)
        painter = QPainter(self)
        color = QColor(self._base.dark(150))
        color.setAlpha(150)
        painter.setPen(color)
        painter.pen().setWidth(2)
        painter.drawPolyline(*tuple(self._SYNTH_POINTS))
        painter = None
        self.drawText()

    def dragEnterEvent(self, e):
        if str(e.mimeData().text()) == 'PatternPart':
            e.acceptProposedAction()

    def dropEvent(self, e):
        e.acceptProposedAction()
        self.pattern = e.mimeData().part.data.copy()
        
    def copy(self):
        newpart = Part.copy(self)
        if self.pattern:
            newpart.pattern = self.pattern.copy()
        return newpart

    def activate(self, on):
        if on:
            self.activeLED.flashing()
        else:
            self.activeLED.stop()


_EFFECT_POINTS = []
for i in range(5):
    x = random.randint(55, spec.PART_WIDTH - 10)
    y = random.randint(10, spec.PART_HEIGHT - 10)
    _EFFECT_POINTS.append(QPoint(x, y))


class EffectPart(Part):
    def __init__(self, effect, parent=None):
        Part.__init__(self, effect, parent)
        self.base_color(QColor('blue'))

    def paintEvent(self, e):
        Part.paintEvent(self, e)
        painter = QPainter(self)
        color = QColor(self._base)
        color.setAlpha(200)
        painter.setPen(color.dark(150))
        painter.setBrush(color.dark(115))
        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawEllipse(11, 22, 10, 10)
        
        rect = QRectF(25, 17, 7, 20)
        painter.drawChord(rect, 270 * 16, 180 * 16)
        
        rect = QRectF(40, 11, 10, 30)
        painter.drawChord(rect, 270 * 16, 180 * 16)

        painter.drawEllipse(63, 14, 5, 5)
        painter.drawEllipse(63, 35, 5, 5)
        painter.drawEllipse(81, 14, 5, 5)
        painter.drawEllipse(81, 35, 5, 5)
        
        painter = None
        self.drawText()


class PatternPart(Part):

    def __init__(self, pattern_, parent=None):
        Part.__init__(self, pattern_, parent)
        self.base_color(QColor('orange'))

    def paintEvent(self, e):
        Part.paintEvent(self, e)
        if not self.data is None:
            painter = QPainter(self)
            color = QColor(self._base.dark(150))
            color.setAlpha(150)
            painter.setPen(color)
            painter.setBrush(color)

            x_px = self.width() / (self.data.beats * 64.0)
            for note in self.data:
                x = note.start * x_px
                y = self.height() - (note.pitch / 127.0) * self.height()
                w = (note.stop - note.start) * x_px
                painter.drawRect(x, y, w, 1)
            painter = None
        if self.data:
            self.drawText(self.data.name)


if __name__ == '__main__':
    from PyQt4.QtGui import QWidget, QGridLayout
    from pk.widgets.utils import run_widget
    import scsynth
    class Glob(QWidget):
        def __init__(self):
            QWidget.__init__(self)
            Layout = QGridLayout(self)
            
            synthpart = SynthPart(None, self)
            synthpart.selected = True
            synthpart.activated(True)
            Layout.addWidget(synthpart, 0, 0)
            
            effectpart = EffectPart(None, self)
            Layout.addWidget(effectpart, 0, 1)
            
            self.pattern = scsynth.Pattern()
            self.pattern.beats = 4
            for i in (0, 64, 128, 196):
                stop = i + random.randint(16, 32)
                pitch = random.randint(32, 96)
                self.pattern.add(sequencer.Note(i, stop, pitch))
            Layout.addWidget(PatternPart(self.pattern, self), 1, 0)
    run_widget(Glob)

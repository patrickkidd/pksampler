
from PyQt4.QtCore import *
from PyQt4.QtGui import *


class ScrollPad(QAbstractSlider):
    def __init__(self, parent=None):
        QAbstractSlider.__init__(self, parent)
        self.setMouseTracking(False)
        self._value = 0.0

    def mousePressEvent(self, e):
        self._last_y = e.y()
        
    def mouseMoveEvent(self, e):
        diff = e.y() - self._last_y
        diff /= 8.0
        self._last_y = e.y()
        
        self._value += diff
        if self._value > self.maximum():
            self._value = float(self.maximum())
        elif self._value < self.minimum():
            self._value = float(self.minimum())
        self.setValue(self._value)
        self.update()
        self.emit(SIGNAL('valueChanged(int)'), self.value())

    def mouseReleaseEvent(self, e):
        self._last_y = None

    def paintEvent(self, e):
        painter = QPainter(self)
        percent = self.value() / float(self.maximum())
        if percent == 1:
            percent = .9999
        elif percent == 0:
            percent = .0001
        low = percent - .1
        mid = percent
        high = percent + .1

        if low < 0:
            low = 0.0
        if high > 1:
            high = 1.0
        
        base = QColor('green').dark(175)
        base.setAlpha(180)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(low, base.light(300))
        gradient.setColorAt(mid, base)
        gradient.setColorAt(high, base.light(300))
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, 0, self.width(), self.height())
        

class ScrollBar(QAbstractSlider):

    box_height = 40

    def __init__(self, parent=None):
        QAbstractSlider.__init__(self, parent)
        self.setFixedWidth(50)
        self.setTracking(True)
        self._last_y = 0
        
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setPen(self.palette().color(QPalette.Mid))
        painter.setBrush(self.palette().color(QPalette.Dark))

        y = self.value() - (self.box_height / 2)
        if y < 0:
            y = 0
        elif y > self.height() - self.box_height:
            y = self.height() - self.box_height
        painter.drawRect(0, y, self.width(), self.box_height)

    def resizeEvent(self, e):
        self.setMaximum(self.height())

    def mousePressEvent(self, e):
        self._last_y = 0
        self.setSliderDown(True)

    def mouseReleaseEvent(self, e):
        self.setSliderDown(False)

    def over_handle(self, e):
        y = self.value() - (self.box_height / 2)
        if y < 0:
            y = 0
        elif y > self.height() - self.box_height:
            y = self.height() - self.box_height
        return e.y() >= y or e.y() <= y + self.box_height

    def mouseMoveEvent(self, e):
        v = (e.y() - self.box_height / 2.0) / (self.height() - self.box_height) * self.maximum()
        self.setValue(v)
        self.update()
        self.emit(SIGNAL('valueChanged(int)'), self.value())



if __name__ == '__main__':
    app = QApplication([])

    parent = QWidget()
    parent.show()
    parent.resize(300, 300)
    Layout = QHBoxLayout(parent)

    w = QLabel()
    pixmap = QPixmap('/Users/patrick/repos.tulkas/pixmaps/icons/clover.png')
    w.setPixmap(pixmap)
    w.setScaledContents(True)
    w.resize(600, 600)

    scrollarea = QScrollArea(parent)
    scrollarea.setWidget(w)
    Layout.addWidget(scrollarea)

    scrollbar = ScrollPad(parent)
    scrollbar.setMinimumWidth(100)
    Layout.addWidget(scrollbar)

    scrollarea.verticalScrollBar().setMaximum(10000)
    print scrollarea.verticalScrollBar().maximum()
    def scroll(value):
        percent = value / float(scrollbar.maximum())
        sb = scrollarea.verticalScrollBar()
        sb.setValue(sb.maximum() * percent)
        
    QObject.connect(scrollbar, SIGNAL('valueChanged(int)'), scroll)

    app.exec_()
    

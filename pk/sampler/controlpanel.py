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
Global-ish controls
"""

from PyQt4.QtCore import QObject, SIGNAL
from PyQt4.QtGui import QFrame, QVBoxLayout, QButtonGroup
import pk.widgets
import pk.widgets.utils
import midi
import spec
import slots


class ControlPanel(QFrame):
    def __init__(self, parent=None, channels=8):
        QFrame.__init__(self, parent)
        self.setFrameShape(spec.FRAME_SHAPE)
        self.setAutoFillBackground(True)
        self.palette().setColor(self.backgroundRole(),
                                spec.POV_COLOR)

        self.mapper = midi.InputWidget(parent=self)
        self.mapper.setMinimumHeight(50)
        self.send1Slot = slots.EffectSlot(self)
        self.send2Slot = slots.EffectSlot(self)
        
        self.modeGroup = QButtonGroup(self)
        self.modeGroup.setExclusive(True)
        self.modeButtons = []
        for mode in ('select', 'play', 'delete'):
            button = pk.widgets.Button(self)
            button.setText(mode)
            button.setCheckable(True)
            setattr(self, mode+'Button', button)
            self.modeGroup.addButton(button)
            self.modeButtons.append(button)

        QObject.connect(self.send1Slot, SIGNAL('selected(QWidget *)'),
                        self, SIGNAL('selected(QWidget *)'))
        QObject.connect(self.send2Slot, SIGNAL('selected(QWidget *)'),
                        self, SIGNAL('selected(QWidget *)'))

        Layout = QVBoxLayout(self)
        Layout.addWidget(self.mapper)
        Layout.addStretch(1)
        pk.widgets.utils.h_centered(Layout, self.send1Slot)
        pk.widgets.utils.h_centered(Layout, self.send2Slot)
        for button in self.modeButtons:
            pk.widgets.utils.h_centered(Layout, button)


if __name__ == '__main__':
    import pk.widgets.utils
    pk.widgets.utils.run_widget(ControlPanel)

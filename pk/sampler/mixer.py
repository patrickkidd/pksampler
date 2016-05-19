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
REQUIREMENTS
------------
 - channels: volume, pan, send1, send2
 - synths: start/stop
 - drag synths => channels
 - drag patterns => synths
 - drag effects => send1, send2
 - beat match tempo
 - settings:
   - mode: play,delete
"""

from pk.widgets import Button
from PyQt4.QtCore import QObject, SIGNAL, Qt
from PyQt4.QtGui import QFrame, QVBoxLayout, QGridLayout, QPainter, QColor, QHBoxLayout, QButtonGroup
import pk.widgets
import pk.widgets.utils
import rtplayer
import controlpanel
import keyboard
import toolbox
import spec
import slots
import parts


SYNTHS = 3


class ChannelControls(QFrame):
    """ Volume, knobs. """
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setAutoFillBackground(True)
        self.setFrameShape(spec.FRAME_SHAPE)
        self.setFrameShadow(QFrame.Sunken)
        self.palette().setColor(self.backgroundRole(),
                                pk.widgets.utils.POV_COLOR)

        self.knobs = pk.widgets.Knobs(knobs=3, parent=self)
        self.panKnob = self.knobs.knobs[0]
        self.send1Knob = self.knobs.knobs[1]
        self.send2Knob = self.knobs.knobs[2]
        self.volumeSlider = pk.widgets.MixerSlider(self)

        Layout = QVBoxLayout(self)
        Layout.setSpacing(0)
        Layout.setMargin(0)
        pk.widgets.utils.h_centered(Layout, self.knobs)
        pk.widgets.utils.h_centered(Layout, self.volumeSlider)


class MainWindow(QFrame):
    def __init__(self, engine, parent=None, channels=4):
        QFrame.__init__(self, parent)
        self.setAutoFillBackground(True)
        self.palette().setColor(self.backgroundRole(),
                                spec.BACKGROUND)

        self.controlPanel = controlpanel.ControlPanel(self)

        self.keyboard = keyboard.Keyboard(self, orientation=Qt.Vertical)
        self.keyboard.keywidth = 25
        self.keyboard.setHalfSteps(127)
        self.keyboard.setMinimumWidth(50)
        
        self.controls = []
        self.synthzones = []
        MixerLayout = QHBoxLayout()
        for i in range(channels):
            ChannelLayout = QVBoxLayout()
            for j in range(SYNTHS):
                synthzone = slots.SynthSlot(self)
                QObject.connect(synthzone, SIGNAL('selected(QWidget *)'),
                                self.clicked)
                synthzone.channel = i
                ChannelLayout.addWidget(synthzone)
            controls = ChannelControls(self)
            controls.channel = i
            ChannelLayout.addWidget(controls)
            MixerLayout.addLayout(ChannelLayout)

        self.toolbox = toolbox.ToolBox(self)
        self.toolbox.setFrameShape(spec.FRAME_SHAPE)
        self.toolbox.setFixedWidth(spec.PART_WIDTH + spec.SCROLLPAD_WIDTH + 10)

        self.engine = engine
        self.rtplayer = rtplayer.RTPlayer(engine.server)
        self.rt_note = None
        self.current_synth = None
        self.mode = None
        self.set_mode('select')
        self.notes = {}

        QObject.connect(self.controlPanel.modeGroup,
                        SIGNAL('buttonClicked(QAbstractButton *)'),
                        self.mode_clicked)
        QObject.connect(self.keyboard,
                        SIGNAL('noteon(int, int)'),
                        self.noteon)
        QObject.connect(self.keyboard,
                        SIGNAL('noteoff(int, int)'),
                        self.noteoff)

        Layout = QHBoxLayout(self)
        Layout.addWidget(self.controlPanel)
        Layout.addWidget(self.keyboard)
        Layout.addLayout(MixerLayout)
        Layout.addWidget(self.toolbox)

    def slotVolume(self, chan, value):
        self.emit(SIGNAL('volume(int, float)'),
                  self.channels.index(chan), value)

    def mode_clicked(self, button):
        self.set_mode(str(button.text()))

    def set_mode(self, mode):
        self.mode = mode
        getattr(self.controlPanel, mode+'Button').setChecked(True)

    def clicked(self, part):
        if self.current_synth:
            self.current_synth.set_selected(False)

        if self.mode == 'select':
            self.select(part)
        elif self.mode == 'delete':
            part.parent().delete()
            self.current_mode = None
        elif self.mode == 'play':
            self.select(part)
            if part.stream:
                self.engine.deregister(part.stream)
                part.activate(False)
                part.stream = None
            elif part.pattern:
                part.stream = self.engine.register(part.data, part.pattern)
                part.activate(True)

    def select(self, part):
        part.set_selected(True)
        self.current_synth = part
        if isinstance(part, parts.SynthPart):
            self.rtplayer.synth = part.data
        else:
            self.rtplayer.synth = None

    def noteon(self, note, vel):
        """ from editor keyboard """
        note -= 12 * 4
        if self.current_synth:
            synth = self.current_synth.data.copy()
            synth.pitch(note)
            self.rt_note = self.engine.player.play_rt(synth)

    def noteoff(self, note, vel):
        """ from editor keyboard """
        if self.rt_note:
            self.engine.player.stop_rt(self.rt_note)
            self.rt_note = None

    def midi_note(self, msg):
        device, key, vel, timestamp = msg
        if vel:
            self.rtplayer.note_on(key, vel)
        else:
            self.rtplayer.note_off(key, vel)


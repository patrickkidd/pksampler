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
pksampler | supercollider

stream exists

PLAY:
insert pattern

pattern == ringbuffer
engine gobbles 64ths

"""

import time
from PyQt4.QtCore import QObject, SIGNAL, QThread
import scsynth
import threading


class NoteStream(QObject):
    def __init__(self, stream, parent=None):
        QObject.__init__(self, parent)
        self.stream = stream
        self.loop = stream.loop


"""
EventLoop
"""


class Engine(QObject, threading.Thread):
    """ App-level music interface.

    ControlLoop
        inputs: pattern, next_beat, time.time()
        outputs: notes, abs_times

    Emitter
        stream status
        levels?
    
    """
    
    def __init__(self, server, parent=None, verbose=False):
        QObject.__init__(self, parent)
        threading.Thread.__init__(self)
        self.server = server
        self.tempoclock = scsynth.TempoClock(140)
        self.player = scsynth.Player(self.server, verbose=verbose)
        self.loader = scsynth.Loader(self.server, verbose=verbose)
        self.window = scsynth.Window(self.tempoclock)
        self.sequencer = scsynth.Sequencer(self.tempoclock)
        self._timer = None
        self.running = True
        self.qstreams = []

    # event loop

    def stop(self):
        if self.isAlive():
            self.running = False
            self.join()

    def run(self):
        self.running = True
        while self.running:
            self.process()
            # twiddle this value
            self.window.length = self.tempoclock.spb() / 64.0
            time.sleep(self.window.length)

    def process(self):
        """ Process the time window, then adjust the beginning. """
        self.window.update()
        for synth, start, stop, pitch in self.sequencer.render(self.window):
            synth = synth.copy()
            synth.pitch(pitch)
            self.player.play(synth, start, stop)
        self.window.close()

    # sequencer

    def start(self, lead=None, length=None):
        if not self._timer is None:
            self.killTimer(self._timer)
        if lead:
            self.window.lead = lead
        if length:
            self.window.length = length
        self._timer = self.startTimer(self.window.length * 1000)
        threading.Thread.start(self)

    def register(self, synth, pattern):
        stream = self.sequencer.register(synth, pattern)
        qstream = NoteStream(stream)
        self.qstreams.append(qstream)
        return qstream
        
    def deregister(self, qstream):
        qstream.emit(SIGNAL('cursor(int)'), 0)
        self.qstreams.remove(qstream)
        self.sequencer.deregister(qstream.stream)

    def timerEvent(self, e):
        self.emit_status()

    def emit_status(self):
        """ emit app status signals. """
        for qstream in self.qstreams:
            stream = qstream.stream
            step = stream.cursor % (stream.pattern.beats * 64)
            qstream.emit(SIGNAL('cursor(int)'), step)



def metronome():
    import os, sys, time
    from PyQt4.QtCore import SIGNAL
    from PyQt4.QtGui import QApplication, QPushButton, QSlider, QWidget
    from PyQt4.QtGui import QHBoxLayout
    import scsynth
    import synths
    
    app = QApplication(sys.argv)
    server = scsynth.server.start(verbose=True)
    #server = scsynth.server.connect()
    engine = Engine(server, app)
    server.sendMsg('/dumpOSC', 1)
    engine.tempoclock.set_tempo(120)

    SYNTHDEF_PATH = os.path.join(os.path.expanduser('~'),
                                 '.pksampler', 'synthdefs')
    SYNTHDEFS = ('JASStereoSamplePlayer.scsyndef',
                 'JASSine.scsyndef',
                 )
    for fname in SYNTHDEFS:
        engine.server.sendMsg('/d_load', os.path.join(SYNTHDEF_PATH, fname))
    
    CLICK = '/Users/patrick/.pksampler/clicks/click_1.wav'
    engine.loader.load(CLICK)
    time.sleep(.1)

    notes = [scsynth.Note(i, i+16, 69) for i in (0, )]
    pattern = scsynth.Pattern(notes)
    pattern.beats = 1
    stream = engine.register(synths.Sine(), pattern)
    stream.loop(True)
    engine.start()

    widget = QWidget()
    Layout = QHBoxLayout(widget)
    widget.resize(100, 250)
    widget.show()
    
    def set_tempo(value):
        engine.tempoclock.set_tempo(value)
    slider = QSlider(widget)
    slider.setRange(100, 180)
    slider.setValue(140)
    QObject.connect(slider, SIGNAL('valueChanged(int)'), set_tempo)
    Layout.addWidget(slider)

    button = QPushButton('quit', widget)
    QObject.connect(button, SIGNAL('clicked()'), app.quit)
    Layout.addWidget(button)
    
    app.exec_()
    engine.stop()


if __name__ == '__main__':
    metronome()

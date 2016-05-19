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
This is VERY high-level, and simply here for composition's sake.
"""

import os.path
import pk.widgets
import tempo
import selector
import spec


class ToolBox(pk.widgets.ToolBox):
    def __init__(self, parent=None):
        pk.widgets.ToolBox.__init__(self, parent)

        self.synthSelector = selector.Selector(self)
        self.synthScroller = pk.widgets.ScrollArea(self,
                                                   horizontal=False,
                                                   vertical=True,
                                                   color=spec.SCROLLPAD_COLOR)
        self.synthScroller.setWidget(self.synthSelector)
        self.synthScroller.v_pad.setFixedWidth(spec.SCROLLPAD_WIDTH)

        self.effectSelector = selector.Selector(self)
        self.effectScroller = pk.widgets.ScrollArea(self,
                                                    horizontal=False,
                                                    vertical=True,
                                                   color=spec.SCROLLPAD_COLOR)
        self.effectScroller.v_pad.setFixedWidth(spec.SCROLLPAD_WIDTH)
        self.effectScroller.setWidget(self.effectSelector)
        
        self.patternSelector = selector.Selector(self)
        self.patternScroller = pk.widgets.ScrollArea(self, horizontal=False,
                                                   vertical=True,
                                                   color=spec.SCROLLPAD_COLOR)
        self.patternScroller.v_pad.setFixedWidth(spec.SCROLLPAD_WIDTH)
        self.patternScroller.setWidget(self.patternSelector)

        self.tempoAdjuster = tempo.TempoAdjuster(self)
        
        self.addItem(self.synthScroller, 'synths')
        self.addItem(self.effectScroller, 'effects')
        self.addItem(self.patternScroller, 'patterns')
        self.addItem(self.tempoAdjuster, 'tempo')


def frames_per_beat(tempo, samplerate, channels=2):
    bps = float(tempo) / 60 / channels
    return int(samplerate / bps) / 2


import wave
def guess_beats(fpath, filetempo=140):
    wavfile = wave.open(fpath, 'r')
    frames = wavfile.getnframes()
    channels = wavfile.getnchannels()
    samplerate = wavfile.getframerate() * channels
    fpb = frames_per_beat(140, samplerate, channels)
    beats = frames / fpb
    rem = frames % float(fpb)
    if rem > (fpb * .5):
        beats += 1
    return beats


def string_cmp(a, b):
    """ compare strings based on int values. """
    try:
        a = int(a.split()[0])
    except:
        pass
    try:
        b = int(b.split()[0])
    except:
        pass
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0


def load_all(toolbox, loader):
    import scsynth
    import parts, spec, synths
    synths_ = toolbox.synthSelector
    effects = toolbox.effectSelector
    patterns_ = toolbox.patternSelector

    for k, v in synths.__dict__.items():
        if v != scsynth.Synth and type(v) == type(scsynth.Synth) and issubclass(v,scsynth.Synth):
            synths_.add(parts.SynthPart(v()))
    
    fpaths = []
    for fname in os.listdir(spec.SAMPLES):
        if not fname.endswith('.ogg'):
            fpaths.append((os.path.join(spec.SAMPLES, fname), 0))
    for song in os.listdir(spec.LOOPS):
        songpath = os.path.join(spec.LOOPS, song)
        for part in os.listdir(songpath):
            partpath = os.path.join(songpath, part)
            if os.path.isdir(partpath):
                for fname in os.listdir(partpath):
                    if not fname.endswith('.ogg'):
                        fpath = os.path.join(partpath, fname)
                        beats = guess_beats(fpath)
                        fpaths.append((fpath, beats))
    fpaths.sort(string_cmp)
    for fpath, beats in fpaths:
        fname = os.path.basename(fpath)
        sample = synths.Sample()
        if loader:
            sample['bufnum'] = loader.load(fpath)
        part = parts.SynthPart(sample)
        part.text = fname[:fname.find('.')]
        if beats > 0:
            part.text += '\n(%i beats)' % beats
        synths_.add(part)
    effects.add(parts.EffectPart(scsynth.Effect()))
    effects.add(parts.EffectPart(scsynth.Effect()))

    patterns = os.listdir(spec.PATTERNS)
    patterns.sort(string_cmp)
    for fname in patterns:
        if fname.lower().endswith('.xml'):
            fpath = os.path.join(spec.PATTERNS, fname)
            part = parts.PatternPart(scsynth.read_pattern(fpath))
            patterns_.add(part)


if __name__ == '__main__':
    from PyQt4.QtGui import QColor
    import parts
    from pk.widgets.utils import run_widget
    class FakePlayer:
        def load(self, fpath):
            return 0
    class TestToolBox(ToolBox):
        def __init__(self):
            ToolBox.__init__(self)
            self.setAutoFillBackground(True)
            self.palette().setColor(self.backgroundRole(),
                                    QColor(136, 136, 136))
            load_all(self, FakePlayer())
            self.resize(self.width(), 600)
    run_widget(TestToolBox)

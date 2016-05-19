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
Brain folding fuel.

Live timeline editor
 - pattern
  \_ notes
    \_ on, off events

pattern/notes

EVENT POOL
current time
end time
expiration
music time - repr?
control window
play window

NOTE POOL
id pool
"""

import pool


class Synth(dict):
    """ a dict of values, set once per note. """
    
    name = None

    def copy(self):
        ret = self.__class__()
        ret.update(dict.copy(self))
        ret.name = self.name
        return ret

    def pitch(self, pitch):
        """ 0.0 < pitch < n
        nominal: 1.0
        """
        pass


class Effect(Synth):
    pass


class Player:
    """ manage synth and buffer ids for playing synths. """
    def __init__(self, controller, verbose=False):
        self.controller = controller
        self.synth_pool = pool.IntPool(0)
        self.verbose = verbose
        self.controller.sendMsg('/notify', 1)

    def play(self, synth, start, stop):
        self.synth_pool.check()
        sid = self.synth_pool.get(stop+5)
        msg = ['/s_new', synth.name, sid, 1, 0] + list(synth.items())
        for key, value in synth.items():
            msg.extend([key, value])
        if self.verbose:
            print msg
        self.controller.sendBundleAbs(start, [msg])
        self.controller.sendBundleAbs(stop, [['/n_free', sid]])

    def play_rt(self, synth):
        """ """
        self.synth_pool.check()
        sid = self.synth_pool.get()
        msg = ['/s_new', synth.name, sid, 1, 0] + list(synth.items())
        for key, value in synth.items():
            msg.extend([key, value])
        if self.verbose:
            print msg
        self.controller.sendBundleAbs(-1, [msg])
        return sid
        
    def stop_rt(self, sid):
        """ """
        self.controller.sendBundleAbs(-1, [['/n_free', sid]])
        self.synth_pool.recycle(sid)


def main():
    import os
    import time
    import scosc
    import tempoclock
    import loader

    ctl = scosc.Controller(('127.0.0.1', 57110))
    ctl.sendMsg('/dumpOSC', 1)

    SYNTHDEF_PATH = os.path.join(os.path.expanduser('~'), 'scwork', 'synthdefs')
    SYNTHDEFS = ('JASStereoSamplePlayer.scsyndef',
                 'JASSine.scsyndef',
                 )
    for fname in SYNTHDEFS:
        ctl.sendMsg('/d_load', os.path.join(SYNTHDEF_PATH, fname))

    player = Player(ctl)
    loader = ldr.Loader(ctl)
    bid = ldr.load('/Users/patrick/.pksampler/click.wav')

    clock = tempoclock.TempoClock(140.0)

    beats = [clock.spb() * i for i in range(100)]
    now = time.time() + 1
    freqs = [440, 550, 220, 200, 460]
    synth = {'name' : 'JASSine'}
    for seconds in beats:
        abs = now + seconds
        freqs = freqs[1:] + freqs[:1]
        seq.play(synth, abs, abs + 1, freq=freqs[0])


if __name__ == '__main__':
    main()

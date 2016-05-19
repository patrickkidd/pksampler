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
import random
import time
import unittest
import scsynth
from test_tempoclock import Time


random.seed()


class SequencerTest(unittest.TestCase):

    def setUp(self):
        self.localclock = Time()
        self.clock = scsynth.TempoClock(120, localclock=self.localclock)
        self.pattern = scsynth.Pattern()
        for i in (0, 64, 128, 192):
            self.pattern.add(scsynth.Note(i, i+32, 64))
        self.sequencer = scsynth.Sequencer(self.clock)

    def test_register(self):
        stream = self.sequencer.register(None, self.pattern)
        self.assertEqual(self.sequencer.pending[0][0], None)
        self.assertEqual(self.sequencer.pending[0][1], stream)
        self.assertEqual(self.sequencer.pending[0][2], 1)

    def test_deregister(self):
        stream1 = self.sequencer.register(1, self.pattern)
        stream2 = self.sequencer.register(2, self.pattern)

        self.sequencer.deregister(stream1)
        self.sequencer.deregister(stream2)
        self.assertRaises(KeyError, lambda: self.sequencer.deregister(None))

    def test_render(self):
        window = scsynth.Window(self.clock)
        stream = self.sequencer.register(None, self.pattern)
        stream.loop(True)

        window.update()

        notes = self.sequencer.render(window)
        self.assertEqual(len(notes), 3)

        window.close()
        
        self.localclock.value = 1
        window.update()
        notes = self.sequencer.render(window)
        self.assertEqual(len(notes), 2)

        window.close()

        self.localclock.value = 100
        window.update()
        notes = self.sequencer.render(window)
        self.assertEqual(len(notes), 198)

    def test_longtime(self):
        """ make sure all the notes get in there """
        self.clock.set_tempo(150)
        window = scsynth.Window(self.clock)
        stream = self.sequencer.register(None, self.pattern)
        stream.loop(True)

        notes = []
        for i in range(100):
            window.update()
            notes.extend(self.sequencer.render(window))
            window.close()
            self.localclock.value += random.random()

        prev = None
        for index, note in enumerate(notes[1:]):
            if prev:
                try:
                    self.assertAlmostEqual(note[1] - prev[1], .4)
                except AssertionError, e:
                    print 'ERROR ON INDEX:',index + 1
                    raise e
            prev = note


if __name__ == '__main__':
    unittest.main()

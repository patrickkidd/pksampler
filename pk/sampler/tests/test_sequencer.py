import unittest
import time
from pk.sampler import pattern, synths, sequencer, tempoclock
from pk.sampler.tests.test_tempoclock import Time


class NoteStreamTest(unittest.TestCase):

    def setUp(self):
        self.pattern = pattern.Pattern()
        for i in (192, 0, 128, 64):
            self.pattern.add(pattern.Note(i, i+1, 64))
        self.stream = sequencer.NoteStream(self.pattern)

    def test_noloop(self):
        self.stream.loop(False)
        
        notes = self.stream.read(0, 64)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].start, 0)

        notes = self.stream.read(64, 128)
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0].start, 64)
        self.assertEqual(notes[1].start, 128)
        
        notes = self.stream.read(0, 1)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].start, 0)

        notes = self.stream.read(256, 256)
        self.assertEqual(len(notes), 4)
        self.assertEqual(notes[0].start, 256)
        self.assertEqual(notes[1].start, 320)
        self.assertEqual(notes[2].start, 384)
        self.assertEqual(notes[3].start, 448)

        notes = self.stream.read(256, 0)
        self.assertEqual(len(notes), 0)

    def test_noloop_overflow(self):
        self.stream.loop(False)

        notes = self.stream.read(0, 64 * 100)
        self.assertEqual(len(notes), 4)
        self.assertEqual(notes[0].start, 0)
        self.assertEqual(notes[1].start, 64)
        self.assertEqual(notes[2].start, 128)
        self.assertEqual(notes[3].start, 192)

        self.stream.loop(True)
        notes = self.stream.read(0, 64 * 100)
        self.assertEqual(len(notes), 100)
        
    def test_loop(self):
        self.stream.loop(True)

        notes = self.stream.read(0, 64 * 8)
        self.assertEqual(len(notes), 8)
        self.assertEqual(notes[0].start, 0)
        self.assertEqual(notes[1].start, 64)
        self.assertEqual(notes[2].start, 128)
        self.assertEqual(notes[3].start, 192)
        self.assertEqual(notes[4].start, 256)
        self.assertEqual(notes[5].start, 320)
        self.assertEqual(notes[6].start, 384)
        self.assertEqual(notes[7].start, 448)


    def test_loop_whence(self):
        self.stream.loop(True)

        notes = self.stream.read(60, 64 * 8)
        self.assertEqual(len(notes), 8)
        self.assertEqual(notes[0].start, 64)
        self.assertEqual(notes[1].start, 128)
        self.assertEqual(notes[2].start, 192)
        self.assertEqual(notes[3].start, 256)
        self.assertEqual(notes[4].start, 320)
        self.assertEqual(notes[5].start, 384)
        self.assertEqual(notes[6].start, 448)
        self.assertEqual(notes[7].start, 512)

    def test_sparse_noloop(self):
        patt = pattern.Pattern()
        patt.beats = 16
        for i in (192, 0, 128, 1024, 64):
            patt.add(pattern.Note(i, i+1, 64))
        stream = sequencer.NoteStream(patt)
        stream.loop(False)

        notes = stream.read(0, 256)
        self.assertEqual(len(notes), 4)

        notes = stream.read(0, 2000)
        self.assertEqual(len(notes), 5)
        self.assertEqual(notes[4].start, 1024)

        notes = stream.read(0, 10000)
        self.assertEqual(len(notes), 5)
        self.assertEqual(notes[4].start, 1024)


class WindowTest(unittest.TestCase):

    def setUp(self):
        self.localclock = Time()
        self.window = sequencer.Window(tempoclock.TempoClock(120,
                                                             self.localclock))

    def test_update(self):
        """ during processing the window must:
         - start at least 'size' in front of the current time.
         - span at least 'size' seconds.
         - cope with time lapses between calls.
        """
        self.assertEqual(self.window.begin, self.window.end)
        self.assertEqual(self.window.begin, 0)

        # initial
        self.localclock.value = 1
        self.window.update()
        self.assertEqual(1 + self.window.lead + self.window.length,
                         self.window.end)
        self.assertAlmostEqual(self.window.one_step, 0.0078125, 5)
        self.assertEqual(self.window.steps, 384)

        self.window.close()

        # first
        self.localclock.value = 1.1
        self.window.update()
        self.assertEqual(self.window.steps, 12)
        self.assertAlmostEqual(self.window.end, 3.09375, 5)
        end = self.window.begin + self.window.steps * self.window.one_step
        self.assertEqual(self.window.end, end)
        self.assertAlmostEqual(self.window.one_step, 0.0078125, 5)

        self.window.close()

        # second (scaled tempo)
        self.window.clock.set_tempo(150)
        self.localclock.value = 1.2
        self.window.update()
        end = self.window.begin + self.window.steps * self.window.one_step
        self.assertEqual(self.window.end, end)
        self.assertAlmostEqual(self.window.one_step, 0.00625, 5)
        self.assertEqual(self.window.steps, 17)

        self.window.close()

        # third (jump)
        self.localclock.value = 4.5
        self.window.update()
        end = self.window.begin + self.window.steps * self.window.one_step
        self.assertEqual(self.window.end, end)
        self.assertEqual(self.window.steps, 527)
        self.assertAlmostEqual(self.window.one_step, 0.00625, 5)


class SequencerTest(unittest.TestCase):

    def setUp(self):
        self.localclock = Time()
        self.clock = tempoclock.TempoClock(120, localclock=self.localclock)
        self.pattern = pattern.Pattern()
        for i in (0, 64, 128, 192):
            self.pattern.add(pattern.Note(i, i+32, 64))
        self.sequencer = sequencer.Sequencer(self.clock)

    def test_register(self):
        self.clock.localclock.value = 0
        self.clock.update()
        stream = self.sequencer.register(None, self.pattern)
        self.assertEqual(self.sequencer.streams[0][0], None)
        self.assertEqual(self.sequencer.streams[0][1], stream)
        self.assertEqual(self.sequencer.streams[0][2], 1)

        self.clock.localclock.value = 1
        self.clock.update()
        stream = self.sequencer.register(None, self.pattern)
        self.assertEqual(self.sequencer.streams[1][0], None)
        self.assertEqual(self.sequencer.streams[1][1], stream)
        self.assertEqual(self.sequencer.streams[1][2], 3)

        self.clock.localclock.value = 2
        self.clock.update()
        stream = self.sequencer.register(None, self.pattern)
        self.assertEqual(self.sequencer.streams[2][0], None)
        self.assertEqual(self.sequencer.streams[2][1], stream)
        self.assertEqual(self.sequencer.streams[2][2], 5)

    def test_deregister(self):
        stream = self.sequencer.register(None, self.pattern)
        self.sequencer.deregister(stream)
        self.assertRaises(KeyError, lambda: self.sequencer.deregister(None))

    def test_render(self):
        window = sequencer.Window(self.clock)
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

    def test_metronome(self):
        """ test even and predictable timing. """
        self.clock.set_tempo(150)
        window = sequencer.Window(self.clock)
        stream = self.sequencer.register(None, self.pattern)
        stream.loop(True)

        notes = []
        for i in range(4):
            window.update()
            notes.extend(self.sequencer.render(window))
            window.close()
            self.localclock.value += 1

        prev = notes[0]
        for next in notes[1:]:
            #print next[1] - prev[1]
            prev = next

        self.assertAlmostEqual(notes[1][1] - notes[0][1], .4)
        self.assertAlmostEqual(notes[2][1] - notes[1][1], .4)
        self.assertAlmostEqual(notes[3][1] - notes[2][1], .4)
        self.assertAlmostEqual(notes[4][1] - notes[3][1], .4)
        self.assertAlmostEqual(notes[5][1] - notes[4][1], .4)
        self.assertAlmostEqual(notes[6][1] - notes[5][1], .4)
        self.assertAlmostEqual(notes[7][1] - notes[6][1], .4)
        self.assertAlmostEqual(notes[8][1] - notes[7][1], .4)
            


if __name__ == '__main__':
    unittest.main()

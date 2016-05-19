import unittest
from pk.sampler.sequencer import pattern


class XmlTest(unittest.TestCase):
    def test_write_read(self):
        notes = [pattern.Note(i, i+16, 64) for i in (0, 24, 64, 128, 192)]
        p1 = pattern.Pattern(notes)
        p1.beats = 2
        
        pattern.write(p1, 'bleh.xml')
        p2 = pattern.read('bleh.xml')

        self.assertEqual(len(p2), len(p1))
        self.assertEqual(p1[0], p2[0])
        self.assertEqual(p1[1], p2[1])
        self.assertEqual(p1[2], p2[2])
        self.assertEqual(p1[3], p2[3])
        self.assertEqual(p1[4], p2[4])


class PatternTest(unittest.TestCase):
    def test_add(self):
        """ sort all on add """
        self.pattern = pattern.Pattern()
        
        self.pattern.add(pattern.Note(192, 10, 0))
        self.assertEqual(self.pattern[0].start, 192)

        self.pattern.add(pattern.Note(67, 10, 0))
        self.assertEqual(self.pattern[0].start, 67)
        self.assertEqual(self.pattern[1].start, 192)

        self.pattern.append(pattern.Note(60, 10, 0))
        self.assertEqual(self.pattern[0].start, 67)
        self.assertEqual(self.pattern[1].start, 192)
        self.assertEqual(self.pattern[2].start, 60)

        self.pattern.add(pattern.Note(190, 10, 0))
        self.assertEqual(self.pattern[0].start, 60)
        self.assertEqual(self.pattern[1].start, 67)
        self.assertEqual(self.pattern[2].start, 190)
        self.assertEqual(self.pattern[3].start, 192)



if __name__ == '__main__':
    unittest.main()

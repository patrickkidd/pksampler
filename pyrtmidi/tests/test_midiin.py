import os, sys
BUILD_PATH = os.path.join(os.getcwd(), 'build/lib.linux-x86_64-2.4/')
BUILD_PATH = os.path.join(os.getcwd(), 'build/lib.darwin-8.5.0-Power_Macintosh-2.4/')
#print 'Adding',BUILD_PATH
sys.path.append(BUILD_PATH)

import unittest
import rtmidi


class RtMidiInTest(unittest.TestCase):
    def setUp(self):
        self.rtmidi = rtmidi.RtMidiIn()

    def test_01_inputs_exist(self):
        self.assertTrue(self.rtmidi.getPortCount() > 0)

    def test_funcs(self):
        """ test that certain functions can be called. """
        self.rtmidi.openVirtualPort('myport')
        self.rtmidi.ignoreTypes(False, True, False)
        self.rtmidi.closePort()
        for i in range(self.rtmidi.getPortCount()):
            self.rtmidi.getPortName(i)
        
    def test_blocking(self):
        """ test blocking reads. """
        self.rtmidi.openPort(1, True)
        print 'move a MIDI device to send some data...'
        self.rtmidi.getMessage()
        self.rtmidi.getMessage()
        self.rtmidi.getMessage()
        self.rtmidi.closePort()

    def test_non_blocking(self):
        """ test non-blocking reads. """
        self.rtmidi.openPort(1)
        self.rtmidi.getMessage()
        self.rtmidi.getMessage()
        self.rtmidi.getMessage()
        self.rtmidi.closePort()


def print_ports():
    import rtmidi
    midiin = rtmidi.RtMidiIn()

    ports = range(midiin.getPortCount())
    if ports:
        for i in ports:
            print midiin.getPortName(i)
            midiin.openPort(0, True)
            while True:
                print 'MESSAGE:',midiin.getMessage()
    else:
        print 'NO MIDI INPUT PORTS!'


if __name__ == '__main__':
    print_ports()
    #unittest.main()

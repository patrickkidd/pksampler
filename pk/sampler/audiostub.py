"""
Generic high-level audio interfaces. Re-implement each class here.
"""

import time
from PyQt4.QtCore import QObject, QTimer, SIGNAL, QCoreApplication, QEvent


class LevelBus(QObject):
    """ Emits r, p, d signals for level meters.  This can be
    considered a read-only filter that emits levels. Its most
    importand task is to transmit the data in the correct format.
    Contains normalized (0.0 <= x <= 1.0) rms, decay, peak values as
    lists of channels.

    The level emitting should be autonomous from the level
    setting. Implement a timer or something to query the atomic
    values.

    SIGNAL('levelsUpdated()')
    """

    gov_sec = .01
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.interval = 0
        self.rms = [0.0, 0.0]
        self.peak = [0.0, 0.0]
        self.decay = [0.0, 0.0]
        self._last_time = 0

        self.__auto_timer = QTimer(self)
        QObject.connect(self.__auto_timer, SIGNAL('timeout()'),
                        self.__auto_timeout)

    def customEvent(self, e):
        self.rms = e.rms
        self.peak = e.peak
        self.decay = e.decay
        self.emit(SIGNAL('levelsUpdated()'), ())
    
    def toggle_autoPreview(self):
        """ Make the levels go all crazy-like """
        if self.__auto_timer.isActive():
            self.__auto_timer.stop()
        else:
            self.__auto_timer.start(100)

    def __auto_timeout(self):
        import random
        rms = [random.random(), random.random()]
        peak = [random.random(), random.random()]
        delay = [random.random(), random.random()]
        self.set(rms, peak, delay)

    ## public functions
        
    def set(self, rms, peak, decay):
        """ This is the main function, call this from any thread.
        0.0 <= rms, peak, decay <= 1.0
        """
        t = time.time() * 0.1
        if t - self._last_time > self.gov_sec:
            self._last_time = t
            e = QEvent(QEvent.User)
            e.rms = rms
            e.peak = peak
            e.decay = decay
            QCoreApplication.instance().postEvent(self, e)

    def set_interval(self, ms):
        """ the amount of time between signals. """
        self.interval = ms


class Sample(QObject):
    """ Plays a loopable sound on the beat, and at any speed. """
    def __init__(self, parent=None, levelbus=None):
        QObject.__init__(self, parent)
        self.is_playing = False
        self.pitch = 1.0
        self.looping = False
        if levelbus:
            self.levelbus = levelbus
        else:
            self.levelbus = LevelBus(self)

    def load(self, fpath):
        """ samples should be re-usable. """
        pass
    
    def play(self):
        """ """
        self.is_playing = True

    def pause(self):
        """ """
        self.is_playing = False

    def set_pitch(self, pitch):
        """ A float value.
        1.0 == no adjustment
        2.0 == double-tempo.
        """
        self.pitch = pitch
    
    def set_looping(self, on):
        """ Set whether or not the sample should loop when it reaches the end.
        """
        self.looping = bool(on)


class Channel(QObject):
    def __init__(self, parent=None, levelbus=None):
        QObject.__init__(self, parent)
        if levelbus:
            self.levelbus = levelbus
        else:
            self.levelbus = LevelBus(self)
        self.sample = None
        self.volume = 0

    def set_sample(self, sample):
        """ Attach the audio graph elements. """
        self.sample = sample
        
    def set_volume(self, vol):
        """ Set the volume. """
        self.volume = vol

    def set_effect(self, index, value):
        """ Expand on this later... """
        pass

    
class Mixer(QObject):
    """ Connects to the audio hardware. """
    def __init__(self, parent=None, levelbus=None):
        QObject.__init__(self, parent)
        if levelbus is None:
            self.levelbus = LevelBus(self)
        else:
            self.levelbus = levelbus

        self.channels = []

    def attach(self, channel):
        """ Connect a channel to this mixer. """
        self.channels.append(channel)


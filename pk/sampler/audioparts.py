"""
Music-oriented implementation of sequencer engine.
"""


import audioop
import audiostub
import timing


_engine = timing.Engine()
_clock = _engine.clock
_engine.start()


import time
def _atexit():
    time.sleep(1)
    _engine.stop()
import atexit
atexit.register(_atexit)


class ChainSource(timing.SimpleSound):
    def render(self, out_array):
        for o in self.children():
            if isinstance(o, timing.SimpleSound):
                o.render(out_array)


class LevelBus(stub.LevelBus):
    pass


class Channel(stub.Channel, ChainSource):
    def render(self, out_array):
        ChainSource.render(self, out_array)
        out_array *= self.volume


class Mixer(stub.Mixer, ChainSource):
    buffers = {}
    def render(self, out_array):
        for channel in self.channels:
            if not channel in self.buffers:
                self.buffers[channel] = out_array.copy()
                #print 'Mixer: created buffer for',channel
            buf = self.buffers[channel]
            channel.render(buf)
            out_array += buf
            buf *= 0
        self.levelbus.set(*levels(out_array))


def set_main_device(source):
    _engine.add(source)
            

def cpu_load():
    """ "CPU = %.1f%%" % (timing.load() * 100) """
    return _engine.load() * 100


def levels(sound):
    buf = sound.tostring()
    rms = audioop.rms(buf, 2) / 32768.0 # signed
    peak = audioop.avgpp(buf, 2) / 32768.0 # signed
    r = [rms, rms]
    p = [peak, peak]
    d = [0, 0]
    return (r, p, d)


class Sample(stub.Sample, timing.SimpleSound):
    """
    1) Create filter chain concept.
    2) Create LevelBus filter.
    3) Insert LevelBus into chain.
    """
    def __init__(self, parent=None):
        stub.Sample.__init__(self, parent)
        self.source = None

    def render(self, out_array):
        """ Render the source and emit the levels. """
        if self.source:
            self.source.render(out_array)
        else:
            pass
        if self.source and self.source._rolling:
            self.levelbus.set(*levels(out_array))
        timing.SimpleSound.render(self, out_array)

    def load(self, fpath):
        self.source = timing.TimedSound(fpath, _clock)

    def play(self):
        """ play on the next beat """
        beat = _clock._next_spot()
        print 'PLAY %i (NOW == %i)' % (beat, _clock.spot)
        self.source.sched.play_on(beat)

    def pause(self):
        self.source.sched.stop()

    def set_pitch(self, pitch):
        print 'no pitch yet'
        return stub.Sample.set_pitch(self, pitch)

    def set_looping(self, on):
        self.source.sched.looping = True



inline_msg = ''
def print_inline(msg):
    """ iteratively write and over-write a message on the same line. """
    global inline_msg
    # cover out tracks with spaces (weird)
    sys.stdout.write('\b' * len(inline_msg))
    sys.stdout.write(' ' * len(inline_msg))
    sys.stdout.write('\b' * len(inline_msg))
    sys.stdout.write(msg)
    sys.stdout.flush()
    if msg[-1:] == '\n':
        inline_msg = ''
    else:
        inline_msg = msg


def old_main():
    import sys, time, os
    
    HOME = os.environ['HOME']
    FPATH1 = os.path.join(HOME, 'wav/pksampler/bd.wav')
    FPATH2 = os.path.join(HOME, 'wav/pksampler/bass.wav')
    engine = Engine()
    engine.clock.tempo = 137
    engine.start()

    clock = engine.clock

    met = TimedSound(FPATH1, clock)
    met.sched.play_on(0)
    met.sched.looping = True
    engine.add(met)

    buf2 = TimedSound(FPATH2, clock)
    buf2.sched.looping = True
    #buf2.sched.play_on(5)
    engine.add(buf2)

    print '<enter> to play....'
    while True:

        sys.stdin.read(1)    
        buf2.sched.play_on(clock.spot + 2)
        print 'PLAY ON:',clock.spot + 2
        
        #time.sleep(.1)
        #print_inline("callback: CPU = %.1f%%" % (engine.load()*100))


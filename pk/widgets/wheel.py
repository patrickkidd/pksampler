from pixmapwidgets import CyclicSlider


class VerticalWheel(CyclicSlider):
    """ Great jog wheel """
    def __init__(self, parent=None):
        CyclicSlider.__init__(self, parent, 'verticalwheel', 0, 23)
        self.setSingleStep(1)
        self.setPageStep(5)
        self.update()

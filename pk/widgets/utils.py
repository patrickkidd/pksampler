"""
Graphical User Interface functions. This package requires PyQt4.
"""

import os
import sys
from PyQt4.QtGui import QColor, QSpacerItem, QHBoxLayout, QLayout


POV_COLOR = QColor(136, 136, 136)


def h_centered(layout, item):
    l_spacer = QSpacerItem(0, 0)
    r_spacer = QSpacerItem(0, 0)
    proxy = QHBoxLayout()
    proxy.setSpacing(0)
    proxy.setMargin(0)
    proxy.addItem(l_spacer)
    if isinstance(item, QLayout):
        proxy.addLayout(item)
    else:
        proxy.addWidget(item)
    proxy.addItem(r_spacer)
    layout.addLayout(proxy)


HASKDE = False
try:
    raise ImportError # until kde4
    import kdecore
    HASKDE = True
except ImportError:
    pass


def has_kde():
    global HASKDE
    return HASKDE


def run_qt_widget(myclass):
    """ Run a qt widget using QApplication. """
    run_widget(myclass, False)


def run_widget(myclass, use_kde=None):
    """ run a qt app using myclass as the main widget.
    This funtion calls sys.exit().
    """
    global HASKDE
    #pk.options.parse_args()
    #if has_kde() and use_kde is None:
    #    use_kde = pk.options.get('use_kde')
    HASKDE = use_kde
    if use_kde:
        from kdecore import KAboutData, KCmdLineArgs, KApplication
        about = KAboutData('A pk app', 'run_widget', '0.1')
        KCmdLineArgs.init(sys.argv, about)
        a = KApplication()
        w = myclass()
        w.show()
        a.exec_()
    else:
        from PyQt4.QtGui import QApplication
        a = QApplication(sys.argv)
        w = myclass()
        w.show()
        sys.exit(a.exec_())

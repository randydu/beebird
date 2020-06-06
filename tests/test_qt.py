''' test QT5 based GUI '''

from beebird.ui import qt

from . import samples


def test_qt_create():
    ''' test task creator ui '''
    qt.create_task("Hello")

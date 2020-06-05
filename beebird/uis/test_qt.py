''' test QT5 based GUI '''

import beebird
from . import qt


beebird.import_builtin_tasks()


def test_qt_create():
    ''' test task creator ui '''
    qt.create_task("Hello")

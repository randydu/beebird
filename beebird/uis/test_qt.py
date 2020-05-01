
from . import qt

import beebird

beebird.importBuiltinTasks()

def test_qt_create():
    qt.createTask("Hello")
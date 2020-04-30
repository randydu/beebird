
from . import qt
from ..task import Task

Task.importAllTasks()

def test_qt_create():
    qt.createTask("Hello")
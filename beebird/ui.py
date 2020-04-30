''' User interface for tasks management '''

from .task import Task




class TaskUI(object):
    _task: Task = None

    def __init__(self, task):
        self._task = task

    def run(self): pass
''' User interface for tasks management '''

from ..task import Task



class TaskUI: # pylint: disable=too-few-public-methods
    ''' base for all task UI '''
    _task: Task = None

    def __init__(self, task):
        self._task = task

    @property
    def task(self):
        ''' task object bundled with ui '''
        return self._task

"""
Task
"""

from .runner import Runner
from py_json_serialize import json_decode, json_encode

from enum import IntEnum
        
class Task(object):
    """ Basic unit of job """
    class Status(IntEnum):
        """ Task status """
        INIT = 0,  # task is inited, not submitted yet
        SUBMITTED = 1, # submitted, before running
        RUNNING = 2, # being executed
        DONE = 3  # finished, either cancelled, success or failure

    class ErrorCode(IntEnum):
        INVALID = 0, # empty / invalid code
        SUCCESS = 1, # no error
        CANCELLED = 2, # cancelled
        ERROR = 3 # error occurs


    _status = Status.INIT
    _ec = ErrorCode.INVALID 
    _error = None  # task error on failure
    _result = None # task result on success
    _progress: float = 0

    def __init__(self):
        pass

    @property
    def status(self):
        return self._status
    
    @property
    def errcode(self):
        return self._ec

    @property
    def result(self):
        return self._result

    def isProgressAvailable(self):
        return self._progress >= 0

    @property
    def progress(self)->float:
        ''' complete guage [0.0, 1.0] '''
        if self._progress < 0:
            raise RuntimeError('progress not available')

        return self._progress

    @progress.setter
    def progress(self, v:float):
        self._progress = v

    # io
    @staticmethod
    def from_json(jstr: str):
        return json_decode(jstr)

    @staticmethod
    def loadFromFile(fname: str):
        with open(fname, "r") as f:
            jstr = f.read()
        return json_decode(jstr)
    
    def saveToFile(self, fname: str):
        jstr = json_encode(self)
        with open(fname, "w") as f:
            f.write(jstr)

    @staticmethod
    def importAllTasks():
        ''' import all available tasks in qbackup/tasks folder 
        
            the ./tasks/__init__.py will dynamically import all sub-packages
        '''
        from . import tasks



    # run
    def run(self, wait = True):
        """ [sync] execute the task, returns when the task is either done or cancelled """

        self._error = None
        self._result = None
        
        Runner.instance().runTask(self, wait)

    # event listeners
    def onSubmitted(self):
        ''' called when task is submitted to executor engine '''
        self._status = Task.Status.SUBMITTED

    def onRunning(self):
        ''' called when task is being executed by executor engine '''
        self._status = Task.Status.RUNNING

    def onSuccess(self, result):
        ''' called when task is done successfully '''
        self.ErrorCode = Task.ErrorCode.SUCCESS
        self._status = Task.Status.DONE
        self._result = result

    def onError(self, err):
        ''' called when task is done with exception /error '''
        self.ErrorCode = Task.ErrorCode.ERROR
        self._error = err
        self._status = Task.Status.DONE

    def onCancelled(self): 
        ''' called when task is cancelled '''
        self.ErrorCode = Task.ErrorCode.CANCELLED
        self._status = Task.Status.DONE


def task(clsTask):
    ''' 
    class decorator to turn a normal class to a subclass of Task
    
    @task
    class SyncFile:
        ...

    is equalvalent to:

    @json_serialize
    class SyncFile(Task):
        ...

    '''

    from py_json_serialize import json_serialize

    class WrapTask(Task, clsTask):pass

    # simulate the name of input class
    WrapTask.__name__ = clsTask.__name__
    WrapTask.__qualname__ = clsTask.__qualname__

    return json_serialize(WrapTask)

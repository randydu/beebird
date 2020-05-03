"""
Task
"""

from py_json_serialize import json_decode, json_encode, json_serialize
from py_singleton import singleton

from enum import IntEnum

class Group(object):
    ''' task group '''
    def __init__(self, name):
        self.name = name

@singleton
class GroupMan(object):
    ''' group manager '''
    def __init__(self):
        self.groups = {}
    
    def get(self, name:str, createIfNonExistent=True)-> Group:
        ''' get group by name '''
        try:
            g = self.groups[name]
        except KeyError:
            if not createIfNonExistent:
                raise ValueError(f"group '{name}' not found")

            g = Group(name)
            self.groups[name] = g
        
        return g



class MetaInfo(object):
    ''' task meta-info '''
    name = ""  # task name
    group = None
    description = ""
    hidden = False
    system = False

@singleton
class TaskMan(object):
    ''' Task Class Manager '''
    def __init__(self):
        self.tasks = [] # array of task classes
    
    def registerTask(self, clsTask):
        ''' register a task class '''
        if clsTask in self.tasks:
            raise ValueError(f"class '{clsTask.__name__}' already registered!")

        print(f"registering {clsTask.__name__}\r\n")

        self.tasks.append(clsTask)

    def findTaskByName(self, name):
        ''' find registered task class by its name  '''
        for i in self.tasks:
            if i.__name__ == name or ( i._metaInfo_ and i._metaInfo_.name == name):
                return i

        raise ValueError(f"task class name '{name}' not found")

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

    _clsJob_ = None # job class to execute the task
    _metaInfo_ = None # task meta-info

    _status = Status.INIT
    _ec = ErrorCode.INVALID 
    _error = None  # task error on failure
    _result = None # task result on success
    _progress: float = 0

    def __init__(self):
        pass

    @classmethod
    def getJobClass(cls):
        return cls._clsJob_

    @classmethod
    def setJobClass(cls, clsJob):
        if cls._clsJob_:
            raise Exception(f"task ({cls.__name__}) is already binded to job class {cls._clsJob_.__name__}")
        cls._clsJob_ = clsJob

    @classmethod
    def getMetaInfo(cls):
        return cls._metaInfo_

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



    # run
    def run(self, wait = True):
        """ [sync] execute the task, returns when the task is either done or cancelled """

        self._error = None
        self._result = None
        
        cls_job = self.getJobClass()
        if cls_job is None:
            raise ValueError(f"task type ({type(self).__name__}) not supported!")
        
        return cls_job(self).execute(wait)

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


def _task_class(clsTask):
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

    class WrapTask(Task, clsTask):
        def __init__(self,*args,**kwargs):
            Task.__init__(self)
            clsTask.__init__(self, *args,**kwargs)

    # simulate the name of input class
    WrapTask.__name__ = clsTask.__name__
    WrapTask.__qualname__ = clsTask.__qualname__

    TaskMan.instance().registerTask(WrapTask)

    return json_serialize(WrapTask)


def _task_func(func):
    ''' @task decorating function '''

    class WrapTask(Task):
        a = None
        b = None

    tskName = func.__name__
    WrapTask.__name__ = tskName
    WrapTask.__qualname__ = tskName
    TaskMan.instance().registerTask(json_serialize(WrapTask))

    from .job import Job
    class WrapJob(Job):
        def __call__(self):
            return func(a=self._task.a, b = self._task.b)

    WrapTask.setJobClass(WrapJob)

    return func

def task(cls_or_func):
    if isinstance(cls_or_func, type):
        return _task_class(cls_or_func)
    else:
        return _task_func(cls_or_func)
    

# =============================


def run(gui = True):
    jstr = '{ "_clsid_":"DummyTask" }'
    task = Task.from_json(jstr)

    if gui:
        from .uis import qt
        qt.run(task)
    else:
        from .uis import console
        console.run(task)
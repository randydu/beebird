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

        #print(f"registering {clsTask.__name__}\r\n")

        self.tasks.append(clsTask)

    def getTaskByName(self, name):
        ''' find registered task class by its name  '''
        for i in self.tasks:
            if i.__name__ == name or ( i._metaInfo_ and i._metaInfo_.name == name):
                return i

        raise ValueError(f"task class name '{name}' not found")

    def getAllTasks(self):
        ''' get all registered task classes '''
        return self.tasks


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

    _done_callbacks = None # external callbacks called when task is finished.  signature: Callback(task)

    def addDoneCallback(self, cb):
        if self._done_callbacks is None:
            self._done_callbacks = []
        
        if cb in self._done_callbacks:
            raise ValueError('Duplicated done callback')

        self._done_callbacks.append(cb)

    def _callDoneCallbacks(self):
        if self._done_callbacks:
            for cb in self._done_callbacks:
                cb(self)
    

    def __init__(self):
        pass

    @classmethod
    def getJobClass(cls):
        return cls._clsJob_

    @classmethod
    def setJobClass(cls, clsJob):
        if cls._clsJob_ is not None:
            from . import job
            if cls._clsJob != job._CallableTaskJob:
                # external job class binding is allowed only once.
                raise Exception(f"task ({cls.__name__}) is already binded to job class {cls._clsJob_.__name__}")
        cls._clsJob_ = clsJob

    @classmethod
    def getMetaInfo(cls):
        return cls._metaInfo_

    def getFields(self):
        ''' deduce task fields '''
        # both class and object fields are needed to create a task
        cls = type(self)
        cls_fields = [ x for x in dir(cls) if not x.startswith('_') and  type(getattr(cls, x)).__name__ not in ('function', 'method', 'property', 'EnumMeta')]
        obj_fields = [x for x in self.__dict__ if not x.startswith('_')]
        return {*cls_fields, *obj_fields}

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
        """ wait= True, sync, execute the task, returns when the task is either done or cancelled """

        self._error = None
        self._result = None
        
        cls_job = self.getJobClass()
        if cls_job is None:
            raise ValueError(f"task type ({type(self).__name__}) not supported!")

        job = cls_job(self) # pylint: disable=not-callable

        return job.execute(wait)

    # event listeners
    def onSubmitted(self):
        ''' called when task is submitted to executor engine '''
        self._status = Task.Status.SUBMITTED

    def onRunning(self):
        ''' called when task is being executed by executor engine '''
        self._status = Task.Status.RUNNING

    def onSuccess(self, result):
        ''' called when task is done successfully '''
        self._ec = Task.ErrorCode.SUCCESS
        self._status = Task.Status.DONE
        self._result = result

        self._callDoneCallbacks()

    def onError(self, err):
        ''' called when task is done with exception /error '''
        self._ec = Task.ErrorCode.ERROR
        self._error = err
        self._status = Task.Status.DONE

        self._callDoneCallbacks()

    def onCancelled(self): 
        ''' called when task is cancelled '''
        self._ec = Task.ErrorCode.CANCELLED
        self._status = Task.Status.DONE

        self._callDoneCallbacks()

    # --- Operator overloading ---
    
    def __add__(self, tsk):
        ''' task_a + task_b returns parallel task 
        
            task + unity = task
            unity + task = task
        '''

        if id(tsk) == id(unity):
            return self
        else:
            from . import compose
            return compose.Parallel(self, tsk)

    def __mul__(self, tsk):
        ''' task_a * task_b returns serial task 
        
            task + unity = task
            unity + task = task
        '''
        if id(tsk) == id(unity):
            return self
        else:
            from . import compose
            return compose.Serial(self, tsk)


def _task_class(clsTask, public):
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
    WrapTask.__doc__ = clsTask.__doc__

    # if the class object is callable then we assume it is the default Job class to deal with this task.
    # it can be modified by @runtask (in job module)
    if '__call__' in dir(WrapTask):
        from .job import _CallableTaskJob 
        WrapTask.setJobClass(_CallableTaskJob)

    if public:
        TaskMan.instance().registerTask(WrapTask) # pylint: disable=no-member
        return json_serialize(WrapTask)
    else:
        return WrapTask

class Empty(object):
    """ empty default value, with optional annotation """
    def __init__(self, annotation = None):
        super().__init__()
        self.annotation = annotation

""" empty default value without any annotation """
empty = Empty()

def _task_func(func, public):
    ''' @task decorating function 
    
        the function is turned into a task class:

        @task
        def Alarm():
            print("Beep!!!")

        @task
        @def F(a, b): pass

        tsk = Alarm()
        tsk.run()

        Different ways to create the task instance：

        f = A()  # f.a = f.b = inspect.Signature.empty

        f = A(1) # f.a=1 f.b = inspect.Signature.empty

        f = A(1,2) # f.a=1 f.b=2
        f = A(1, b=2) # f.a=1 f.b=2
        f = A(a=1, b=2) # f.a=1 f.b=2

        f.run()
    '''

    import inspect

    params = inspect.signature(func).parameters

    tskName = func.__name__

    def init(self, *args, **kwargs):
        param_names = [*params]
        # pass by position
        for i,v in enumerate(args):
            try:
                self.__setattr__(param_names[i], v)
            except:
                pass
        # pass by kv
        for i in kwargs:
            if i in param_names:
                try:
                    self.__setattr__(i, kwargs[i])
                except:
                    pass

    fields = {}
    for x in params:
        v = params[x].default

        if v == inspect.Signature.empty:
            v = empty

            clsX = params[x].annotation
            if clsX != inspect.Signature.empty:
                v = Empty(clsX)

        fields = {**fields, x:v}


    WrapTask = type(tskName, (Task,), {**fields, **{ '__init__': init, '__doc__': func.__doc__ }})

    if public:
        TaskMan.instance().registerTask(json_serialize(WrapTask)) # pylint: disable= no-member

    from .job import Job
    class WrapJob(Job):
        def __call__(self):
            super().__call__()
            return func.__call__(**{ x: self._task.__getattribute__(x) for x in params })

    WrapTask.setJobClass(WrapJob)

    return WrapTask

def _public_task(cls_or_func):
    if isinstance(cls_or_func, type):
        return _task_class(cls_or_func, True)
    else:
        return _task_func(cls_or_func, True)
    
def _private_task(cls_or_func):
    if isinstance(cls_or_func, type):
        return _task_class(cls_or_func, False)
    else:
        return _task_func(cls_or_func, False)

def task(public = True):
    '''
    # public tasks
    @task
    def Hey():pass
    
    @task(public=True)
    def Hey():pass
    
    @task
    class Hello(object):pass

    @task(True)
    class Hello(object):pass

    # private tasks
    @task(public=False)
    def PrivateHey():pass

    @task(False)
    class PrivateHello(object):pass
    '''

    if isinstance(public, type) or type(public).__name__ == 'function':
        return _public_task(public)

    return _public_task if public else _private_task


# shortcut of private task
task_ = task(False)

# ----- Unity task ------
class _Unity(Task):
    ''' unity task does nothing itself but plays the role of 0 and 1 
    in task composition:

        unity + task = task
        task + unity = task

        unity * task = task
        task * unity = task
    '''
    def run(self, wait = True):pass

    def __add__(self, tsk):
        ''' unity + task returns task '''
        return tsk

    def __mul__(self, tsk):
        ''' unity * task returns task '''
        return tsk


unity = _Unity()

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
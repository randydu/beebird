''' task related decorators '''
import inspect

from py_json_serialize import json_serialize

from .task import Task, TaskMan
from .job import Job, CallableTaskJob, JOB_PARAM


class Empty:  # pylint: disable=too-few-public-methods
    """ empty default value, with optional annotation """

    def __init__(self, annotation=None):
        super().__init__()
        self.annotation = annotation


# empty default value without any annotation
empty = Empty()


def _task_class(cls_task, public):
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

    class Wraptask(Task, cls_task):
        ''' wrapper of decorated class '''

        def __init__(self, *args, **kwargs):
            Task.__init__(self)
            cls_task.__init__(self, *args, **kwargs)

    # simulate the name of input class
    # functools.update_wrapper(Wraptask, cls_task)
    Wraptask.__name__ = cls_task.__name__
    Wraptask.__qualname__ = cls_task.__qualname__
    Wraptask.__doc__ = cls_task.__doc__

    # if the class object is callable then we assume it is the default Job
    # class to deal with this task.
    # it can be modified by @runtask (in job module)
    if '__call__' in dir(cls_task):
        params = inspect.signature(cls_task.__call__).parameters
        has_job_param = JOB_PARAM in params

        def direct_call(self, *, _job_=None):
            #in-thread direct call
            return self(_job_=_job_) if has_job_param else self()

        Wraptask.call = direct_call

        Wraptask.set_job_class(CallableTaskJob)

    if public:
        TaskMan.instance().register(Wraptask)  # pylint: disable=no-member
        return json_serialize(Wraptask)

    return Wraptask


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

    params = inspect.signature(func).parameters
    param_names = [*params]

    has_job_param = False
    if JOB_PARAM in param_names:
        has_job_param = True
        param_names = [i for i in param_names if i != JOB_PARAM]

    task_name = func.__name__

    def init(self, *args, **kwargs):
        # pass by position
        for i, val in enumerate(args):
            try:
                self.__setattr__(param_names[i], val)
            except AttributeError:
                pass
        # pass by kv
        for i in kwargs:
            if i in param_names:
                try:
                    self.__setattr__(i, kwargs[i])
                except AttributeError:
                    pass

    fields = {}

    for name in param_names:
        param = params[name]
        val = param.default

        if val == inspect.Signature.empty:
            val = empty

            cls_x = param.annotation
            if cls_x != inspect.Signature.empty:
                val = Empty(cls_x)

        fields = {**fields, name: val}

    def direct_call(self, *, _job_=None):
        ''' Execute the task in current thread '''
        orig_params = {x: self.__getattribute__(x) for x in param_names}
        if has_job_param:
            return func.__call__(**{JOB_PARAM: _job_, **orig_params})
        return func.__call__(**orig_params)

    wrap_task = type(task_name, (Task,), {
        **fields, **{'__init__': init, 'call': direct_call, '__doc__': func.__doc__}})

    if public:
        # pylint: disable= no-member
        TaskMan.instance().register(json_serialize(wrap_task))

    class WrapJob(Job):
        ''' wrapper job to run the task'''

        def __call__(self):
            super().__call__()
            return self._task.call(_job_=self)


    wrap_task.set_job_class(WrapJob)

    return wrap_task


def _public_task(cls_or_func):
    if isinstance(cls_or_func, type):
        return _task_class(cls_or_func, True)
    return _task_func(cls_or_func, True)


def _private_task(cls_or_func):
    if isinstance(cls_or_func, type):
        return _task_class(cls_or_func, False)
    return _task_func(cls_or_func, False)


def task(public=True):
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

# ------------- JOB DECORATORS --------------------------------------


class runtask:  # pylint: disable=(invalid-name, too-few-public-methods)
    """ class decorator to specify which task type to associate

    ex:

         @runtask(MultiFilesCopy)
         @runtask(SingleFileCopy)
         class FileCopyJob(Job):
             def __call__(self):
                 pass

    """

    def __init__(self, cls_task):
        self._cls_task = cls_task

    def __call__(self, cls_job):
        self._cls_task.set_job_class(cls_job)
        return cls_job


def job(cls_task: Task):
    """ function decorator to turn a function into a job class

    @job(cls_task)
    def upload(task, [_job_]):
        ...

    """

    def wrapper(func):
        class WrapJob(Job):
            ''' job class to run task via decorated function '''

            def __init__(self, tsk):
                super().__init__(tsk)

                params = inspect.signature(func).parameters
                self._has_job_param = JOB_PARAM in params

            def __call__(self):
                super().__call__()

                if self._has_job_param:
                    return func(self._task, _job_=self)
                return func(self._task)

        cls_task.set_job_class(WrapJob)

    return wrapper

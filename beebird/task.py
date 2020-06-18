"""
Task
"""

from enum import IntEnum

from py_json_serialize import json_decode, json_encode
from py_singleton import singleton

from . import job


class Group:  # pylint: disable=too-few-public-methods
    ''' task group '''

    def __init__(self, name):
        self.name = name


@singleton
class GroupMan:  # pylint: disable=too-few-public-methods
    ''' group manager '''

    def __init__(self):
        self.groups = {}

    def get(self, name: str, *, create_if_not_existent=True) -> Group:
        ''' get group by name '''
        try:
            grp = self.groups[name]
        except KeyError:
            if not create_if_not_existent:
                raise ValueError(f"group '{name}' not found")

            grp = Group(name)
            self.groups[name] = grp

        return grp


class MetaInfo:  # pylint: disable=too-few-public-methods
    ''' task meta-info '''
    name = ""  # task name
    group = None
    description = ""
    hidden = False
    system = False


@singleton
class TaskMan:
    ''' Task Class Manager '''

    def __init__(self):
        self.tasks = []  # array of task classes

    def register(self, cls_task):
        ''' register a task class '''
        if cls_task in self.tasks:
            raise ValueError(
                f"class '{cls_task.__name__}' already registered!")

        #print(f"registering {cls_task.__name__}\r\n")

        self.tasks.append(cls_task)

    def find(self, name):
        ''' find registered task class by its name  '''
        for i in self.tasks:
            # pylint: disable=protected-access
            if i.__name__ == name or (i._metaInfo_ and i._metaInfo_.name == name):
                return i

        raise ValueError(f"task class name '{name}' not found")

    def all(self):
        ''' get all registered task classes '''
        return self.tasks


class Task:  # pylint: disable=too-many-public-methods
    """ Base of all tasks """

    class Status(IntEnum):
        """ Task status """
        INIT = 0  # task is inited, not submitted yet
        SUBMITTED = 1  # submitted, before running
        RUNNING = 2  # being executed
        DONE = 3  # finished, either cancelled, success or failure

    class ErrorCode(IntEnum):
        ''' Task's error code '''
        INVALID = 0  # empty / invalid code
        SUCCESS = 1  # no error
        CANCELLED = 2  # cancelled before executing
        STOPPED = 3  # stopped while executing (via job::stop)
        ERROR = 4  # runtime error occurs

    _cls_job_ = None  # job class to execute the task
    _metaInfo_ = None  # task meta-info

    _status = Status.INIT
    _ec = ErrorCode.INVALID
    _error = None  # task error on failure
    _result = None  # task result on success
    _progress: float = 0

    # external callbacks called when task is finished.  signature: Callback(task)
    _done_callbacks = None

    def add_done_callback(self, callback):
        ''' add done event callback '''
        if self._done_callbacks is None:
            self._done_callbacks = []

        if callback in self._done_callbacks:
            raise ValueError('Duplicated done callback')

        self._done_callbacks.append(callback)

    def _call_done_callbacks(self):
        if self._done_callbacks:
            for callback in self._done_callbacks:
                callback(self)

    def __init__(self):
        pass

    @classmethod
    def get_job_class(cls):
        ''' get task associated job class '''
        return cls._cls_job_

    @classmethod
    def set_job_class(cls, cls_job):
        ''' setup task associated job class '''
        if cls._cls_job_ is not None:
            if cls._cls_job_ != job.CallableTaskJob:
                # external job class binding is allowed only once.
                raise Exception(
                    f"task ({cls.__name__}) is already binded to job class "
                    f"{cls._cls_job_.__name__}")
        cls._cls_job_ = cls_job

    @classmethod
    def get_meta_info(cls):
        ''' get task's meta-info '''
        return cls._metaInfo_

    def get_fields(self):
        ''' deduce task fields '''
        # both class and object fields are needed to create a task
        cls = type(self)
        cls_fields = [x for x in dir(cls) if not x.startswith('_') and type(
            getattr(cls, x)).__name__ not in ('function', 'method', 'property', 'EnumMeta')]
        obj_fields = [x for x in self.__dict__ if not x.startswith('_')]
        return {*cls_fields, *obj_fields}

    @property
    def status(self):
        ''' task's current status '''
        return self._status

    @property
    def error_code(self):
        ''' task's error code '''
        return self._ec

    @property
    def error(self):
        ''' task's last exception '''
        return self._error

    @property
    def aborted(self):
        ''' the task is aborted.

            A task can be aborted by calling job::stop():

            mytask = MyTask()
            myjob = mytask.run(wait=True)
            ...
            myjob.stop()

            The output is: the job is either cancelled before execution, or
            stopped prematurely by raising JobStopError while executing by
            job itself.

        '''
        return self._status == Task.Status.DONE and \
            self._ec in [Task.ErrorCode.CANCELLED,
                         Task.ErrorCode.STOPPED]

    @property
    def result(self):
        ''' task's result, available when the associated job is done '''
        if self._ec == Task.ErrorCode.SUCCESS:
            return self._result
        raise ValueError('result is not available on task failure')

    def is_progress_available(self):
        ''' progress feedback '''
        return self._progress >= 0

    @property
    def progress(self) -> float:
        ''' complete guage [0.0, 1.0] '''
        if self._progress < 0:
            raise ValueError('progress not available')

        return self._progress

    @progress.setter
    def progress(self, val: float):
        self._progress = val

    # io
    @staticmethod
    def from_json(jstr: str):
        ''' create task instance from a serialized json string '''
        return json_decode(jstr)

    @staticmethod
    def load_from_file(fname: str):
        ''' load task from a json file '''
        with open(fname, "r") as file:
            jstr = file.read()
        return json_decode(jstr)

    def save_to_file(self, fname: str):
        ''' save task to file in json format '''
        jstr = json_encode(self)
        with open(fname, "w") as file:
            file.write(jstr)

    # run
    def run(self, wait=True):
        """ Execute the task in thread pool

            SYNC (wait=True): returns when the task is either done or cancelled
            ASYNC (wait=False): returns the job instance to run the task.
        """

        self._error = None
        self._result = None

        cls_job = self.get_job_class()
        if cls_job is None:
            raise ValueError(
                f"task type ({type(self).__name__}) not supported!")

        job_ = cls_job(self)  # pylint: disable=not-callable
        return job_.execute(wait)

    # event listeners
    def on_submitted(self):
        ''' called when task is submitted to executor engine '''
        self._status = Task.Status.SUBMITTED

    def on_running(self):
        ''' called when task is being executed by executor engine '''
        self._status = Task.Status.RUNNING

    def on_success(self, result):
        ''' called when task is done successfully '''
        self._ec = Task.ErrorCode.SUCCESS
        self._status = Task.Status.DONE
        self._result = result

        self._call_done_callbacks()

    def on_error(self, err):
        ''' called when task is done with exception /error '''
        if isinstance(err, job.JobStopError):
            self._ec = Task.ErrorCode.STOPPED
        else:
            self._ec = Task.ErrorCode.ERROR
        self._error = err
        self._status = Task.Status.DONE

        self._call_done_callbacks()

    def on_cancelled(self):
        ''' called when task is cancelled '''
        self._ec = Task.ErrorCode.CANCELLED
        self._status = Task.Status.DONE

        self._call_done_callbacks()

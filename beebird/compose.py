""" Task Composition

    task can be executed in parallel, in serial order or even combined;
    task may be skipped at runtime under some conditions;
    task can be repeated, delayed;

    This module implements the building blocks to compose tasks into a single task.

"""

import threading
import collections
import copy
import time
import queue

from beebird.task import Task
from beebird.job import Job, JobStopError
from beebird.decorators import runtask


def _flatten(tasks, cls) -> list:
    ''' flatten the nesting serial/parallel tasks '''
    result = []
    for i in tasks:
        if isinstance(i, cls):
            result.extend(i._tasks)  # pylint: disable=protected-access
        else:
            result.append(i)

    return result

def _resolve_task(cls_or_task)->Task:
    ''' resolve a task instance '''
    if isinstance(cls_or_task, Task):
        return cls_or_task
    if issubclass(cls_or_task, Task):
        return cls_or_task()
    raise ValueError('input must be a task object or a subclass of Task')


class Parallel(Task):
    ''' execute tasks in parallel

        task = Parallel(tA, tB, tC)
        task.run()  # tA, tB, tC runs in parallel

        assert task.result == [ tA.result, tB.result, tC.result ]
    '''

    def __init__(self, *tasks):
        super().__init__()
        self._tasks = _flatten([_resolve_task(i) for i in tasks], Parallel)


@runtask(Parallel)
class _ParalletJob(Job):
    # maximum waiting time for status checking.
    MAX_WAIT_SECONDS = 1000

    def __init__(self, task):
        super().__init__(task)

        self._cv = threading.Condition()
        self._count = 0
        self._total = 0
        self._error = None

    def task_done_callback(self, task):  # pylint: disable=unused-argument
        ''' called when task is done '''
        with self._cv:
            if task.aborted:
                self._stop = True
            elif task.error_code == Task.ErrorCode.ERROR:
                self._error = task.error
            else:  # success
                self._count += 1

            self._cv.notify()

    def __call__(self):
        super().__call__()

        tasks = self._task._tasks

        self._total = len(tasks)
        self._count = 0
        self._task.progress = 0

        if self._total > 0:
            jobs = []
            for i in tasks:
                i.add_done_callback(self.task_done_callback)
                jobs.append(i.run(wait=False))

            while True:
                with self._cv:
                    if self._stop or self._error:
                        for job_ in jobs:
                            job_.stop()

                        if self._error:
                            raise self._error

                        raise JobStopError()

                    self._task.progress = self._count / self._total

                    if self._count == self._total:
                        break

                    self._cv.wait(_ParalletJob.MAX_WAIT_SECONDS)

        return [t.result for t in tasks]


# ----------- Serial -------------

class Serial(Task):
    ''' execute tasks in serial '''

    def __init__(self, *tasks):
        super().__init__()
        self._tasks = _flatten([_resolve_task(i) for i in tasks], Serial)


@runtask(Serial)
class _SerialJob(Job):
    ''' execute task one by one.

        Returns: array of results in order of task execution on success,
        raises the exception of first task on error.
    '''

    def __call__(self):
        super().__call__()

        tasks = self._task._tasks

        total = len(tasks)
        self._task.progress = 0

        results = []
        if total > 0:
            count = 0
            for i in tasks:
                i.run(wait=True)

                if self._stop or i.aborted:
                    raise JobStopError()

                if i.error_code == Task.ErrorCode.ERROR:
                    raise i.error

                # success
                results.append(i.result)
                count += 1
                self._task.progress = count / total

        return results


# ----- Unity task ------

class _Unity(Task):
    ''' unity task does nothing itself but plays the role of 0 and 1
    in task composition:

        unity + task = task
        task + unity = task

        unity * task = task
        task * unity = task
    '''

    def run(self, wait=True):
        ''' do nothing '''
        self.on_success(None)

    def __add__(self, tsk):
        ''' unity + task returns task '''
        return tsk

    def __mul__(self, tsk):
        ''' unity * task returns task '''
        return tsk


unity = _Unity()

# --- Task Operator overloading ---


def _add_task(self, tsk):
    ''' task_a + task_b returns parallel task

        task + unity = task
        unity + task = task
    '''

    if id(tsk) == id(unity):
        return self

    return Parallel(self, tsk)


def _mul_task(self, tsk):
    ''' task_a * task_b returns serial task

        task + unity = task
        unity + task = task
    '''
    if tsk is unity:
        return self

    return Serial(self, tsk)


Task.__add__ = _add_task
Task.__mul__ = _mul_task

# ------- bucket --------
_TaskDep = collections.namedtuple('TaskDep', ['task', 'pre_tasks'])


class Bucket(Task):
    ''' interelated tasks '''

    def __init__(self):
        super().__init__()
        self.task_deps = {}  # id: TaskDep

    def add(self, tsk: Task, pre_tasks: list = None):
        ''' adds a task with pre-tasks '''
        if pre_tasks:
            for i in pre_tasks:
                task_id = id(i)
                if task_id not in self.task_deps:
                    self.task_deps[task_id] = _TaskDep(i, [])

        pre_tasks = pre_tasks or []
        task_id = id(tsk)
        try:
            tdp = self.task_deps[task_id]
        except KeyError:
            self.task_deps[task_id] = _TaskDep(tsk, pre_tasks)
        else:
            if tdp.pre_tasks == []:
                # previously defined as task dependency
                if pre_tasks:
                    tdp.pre_tasks.append(*pre_tasks)
            else:
                if tdp.pre_tasks != pre_tasks:
                    raise ValueError(f'"{type(tsk).__name__}"'
                                     ' task dependency conflict'
                                     )

    def find_loop(self):
        ''' check loopback, return True if loopback is found '''

        checked = []  # no loop

        class LoopError(Exception):
            ''' loopback error '''

        def search(tdp, path):
            if tdp.pre_tasks:
                if tdp.task in path:
                    raise LoopError()

                path.append(tdp.task)

                for tsk in tdp.pre_tasks:
                    if tsk not in checked:
                        search(self.task_deps[id(tsk)], path + [tsk])
            checked.append(tdp.task)

        try:
            for tdp in self.task_deps.values():
                if tdp.task not in checked:
                    search(tdp, [])
            return False
        except LoopError:
            return True

    def find_leaf_tasks(self):
        ''' get tasks without any pre-tasks '''
        return [tdp.task for tdp in self.task_deps.values() if not tdp.pre_tasks]

    def remove_tasks(self, tasks):
        ''' remove tasks from bucket '''
        for tsk in tasks:
            del self.task_deps[id(tsk)]

    def decimate_pre_task(self, pre_task):
        ''' remove the pre-task from all of the its dependent tasks.

            usually called when the pre_task is done so its dependent tasks
            can be available for execution if no more pre-tasks exist.
        '''
        for tdp in self.task_deps.values():
            if pre_task in tdp.pre_tasks:
                tdp.pre_tasks.remove(pre_task)

    def clear(self):
        ''' remove all tasks '''
        self.task_deps = {}

    def run(self, wait=True):
        ''' run the tasks in this bucket '''
        if self.find_loop():
            raise ValueError('bucket has loopback')

        return super().run(wait)

    @property
    def total(self):
        ''' total tasks in bucket '''
        return len(self.task_deps)


@runtask(Bucket)
class _BucketJob(Job):
    ''' job executing tasks in a bucket '''
    MAX_WAIT_SECONDS = 1

    def __init__(self, task: Bucket):
        super().__init__(task)

        self._cv = threading.Condition()
        self._stop = False

        self._total = self._task.total  # total tasks in bucket
        self._count = 0  # total successful tasks
        self._jobs = {}  # running jobs, task_id => submitted job

        self._error_task = None  # task done with error (first one)

    def task_done_callback(self, task):  # pylint: disable=unused-argument
        ''' called when task is done '''
        with self._cv:
            try:
                del self._jobs[id(task)]
            except KeyError:
                pass

            if task.error_code == Task.ErrorCode.SUCCESS:
                self._task.decimate_pre_task(task)
                self._count += 1
            elif task.aborted:
                self._stop = True
            else:  # on error
                if self._error_task is None:  # first exception only
                    self._error_task = task

            self._cv.notify()

    def __call__(self):
        super().__call__()

        bkt = self._task

        while True:
            with self._cv:

                self._task.progress = self._count / self._total

                if self._total == self._count:  # empty, done.
                    break

                if self._stop or self._error_task:
                    # a task ends abnormally, exiting the bucket execution
                    for i in self._jobs:
                        i.stop()

                    # ?? should we wait for the ending of all running jobs
                    # ?? before return?

                    if self._error_task:
                        raise self._error_task.error

                    # this job is stopped.
                    raise JobStopError()

                tasks = bkt.find_leaf_tasks()
                if tasks:
                    bkt.remove_tasks(tasks)
                    for i in tasks:
                        i.add_done_callback(self.task_done_callback)
                        self._jobs[id(i)] = i.run(wait=False)  # job

                self._cv.wait(_BucketJob.MAX_WAIT_SECONDS)


# -------------- Control Flow --------------

class do(Task): # pylint: disable=invalid-name
    ''' do then catch '''

    def __init__(self, task_cond):
        super().__init__()
        self._then = [_resolve_task(task_cond)]
        self._catch = None

    def then(self, task_then):
        ''' run the task if all preceding tasks are done successfully '''
        self._then.append(_resolve_task(task_then))
        return self

    def catch(self, task_catch):
        ''' error handler '''
        self._catch = _resolve_task(task_catch)
        return self


@runtask(do)
class _JobDo(Job):
    MAX_WAIT_SECONDS = 1

    def __init__(self, task):
        super().__init__(task)

        self._event = threading.Event()

    def _on_tasks_done(self, _):
        ''' called when the then tasks are done '''
        self._event.set()  # wake up

    def __call__(self):
        super().__call__()

        then = self._task._then
        total = len(then)
        if total == 0:
            return None, None

        tsk = then[0] if total == 1 else Serial(*self._task._then)
        tsk.add_done_callback(self._on_tasks_done)
        job_ = tsk.run(wait=False)

        while True:
            if self._stop:
                job_.stop()
                raise JobStopError()

            if tsk.status == Task.Status.DONE:
                if tsk.aborted:
                    raise JobStopError()

                if tsk.error_code == Task.ErrorCode.SUCCESS:
                    return tsk.result

                # runs error handler
                handler = self._task._catch
                if handler is None:
                    raise tsk.error  # no error handler

                handler.err = tsk.error  # sets the error to handle
                handler.run(wait=True)  # sync

                if handler.error_code == Task.ErrorCode.SUCCESS:
                    return handler.result

                return handler.error

            self._event.wait(_JobDo.MAX_WAIT_SECONDS)

# ---------- safe_run ---------
class TryRun(Task):
    ''' try running a task until it is done successfully.

        max_tries: maximum tries (default = 3)
                  if maximum == 0: unlimited tries

        sleep_seconds: sleep time before another try. (default: 1 seconds)
                      0: no sleep
        returns task result on success, otherwise error of last run is raised.
    '''
    def __init__(self, tsk, *, max_tries=3, sleep_seconds=1):
        super().__init__()
        self._task = _resolve_task(tsk)

        if max_tries < 0:
            raise ValueError('max_tries must >=0')
        self._max_tries = max_tries

        if sleep_seconds < 0:
            raise ValueError('sleep_seconds must >=0')
        self._sleep_seconds = sleep_seconds

@runtask(TryRun)
class _TryRunJob(Job):
    def __call__(self):
        super().__call__()

        max_tries = self._task._max_tries
        sleep_seconds = self._task._sleep_seconds
        count = 0

        task_orig = self._task._task
        while True:
            if self._stop:
                raise JobStopError()

            tsk = copy.copy(task_orig)
            tsk.run(wait=True)
            if tsk.error_code == Task.ErrorCode.SUCCESS:
                return tsk.result

            count += 1
            if 0 < max_tries <= count:
                raise tsk.error

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

# ------------ FIFO ------------------
class FIFO(Task):
    ''' first in first out task queue.

        FIFO is different from Serial in that it will not not terminate
        until stopped.
    '''

    MAX_WAIT_SECONDS = 1

    def __init__(self, max_queue_size=10, max_wait_seconds=MAX_WAIT_SECONDS):
        super().__init__()
        self._tasks = queue.Queue(maxsize=max_queue_size)
        self._max_wait_seconds = max_wait_seconds

    def check_status(self):
        ''' make sure the FIFO is still working properly '''
        if self._status == Task.Status.DONE:
            # FIFO can be done either when one of task raise error,
            # or it is cancelled.
            raise self._error

    def add(self, tsk: Task)->bool:
        ''' adds a task to the queue '''
        try:
            self.check_status()
            self._tasks.put(tsk, block=True, timeout=self._max_wait_seconds)
            return True
        except queue.Full:
            return False

    def get(self)->Task:
        ''' try retrieving a task.

            return a task if within a maximum period (1 second), or None
            if no task available during this time period.
        '''
        try:
            self.check_status()
            return self._tasks.get(block=True, timeout=self._max_wait_seconds)
        except queue.Empty:
            return None

@runtask(FIFO)
class _FIFOJob(Job):
    def __call__(self):
        super().__call__()

        task = self._task

        while True:
            self.check_stop()

            tsk = task.get()
            if tsk:
                tsk.run(wait=True)
                if tsk.error_code != Task.ErrorCode.SUCCESS:
                    raise tsk.error

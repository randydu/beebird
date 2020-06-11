""" Task Composition

    task can be executed in parallel, in serial order or even combined;
    task may be skipped at runtime under some conditions;
    task can be repeated, delayed;

    This module implements the building blocks to compose tasks into a single task.

"""

import threading
import collections

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


class Parallel(Task):
    ''' execute tasks in parallel

        task = Parallel(tA, tB, tC)
        task.run()  # tA, tB, tC runs in parallel

        assert task.result == [ tA.result, tB.result, tC.result ]
    '''

    def __init__(self, *tasks):
        super().__init__()
        self._tasks = _flatten(tasks, Parallel)


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
        self._tasks = _flatten(tasks, Serial)


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

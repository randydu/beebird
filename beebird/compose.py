""" Task Composition

    task can be executed in parallel, in serial order or even combined;
    task may be skipped at runtime under some conditions;
    task can be repeated, delayed;

    This module implements the building blocks to compose tasks into a single task.

"""

import threading
import collections

from beebird.task import Task
from beebird.job import Job
from beebird.decorators import runtask


def _flatten(tasks, cls):
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
    def __init__(self, task):
        super().__init__(task)

        self._cv = threading.Condition()
        self._count = 0
        self._total = 0

    def task_done_callback(self, task):  # pylint: disable=unused-argument
        ''' called when task is done '''
        with self._cv:
            self._count -= 1

            self._task.progress = 1 - self._count / self._total

            if self._count == 0:
                self._cv.notify()

    def __call__(self):
        super().__call__()

        tasks = self._task._tasks

        for i in tasks:
            i.add_done_callback(self.task_done_callback)
            self._count += 1

        self._total = self._count
        self._task.progress = 0

        if self._total > 0:
            with self._cv:
                for i in tasks:
                   # print(f"submit task {i}")
                    i.run(wait=False)

                # print("waiting all task done...")
                self._cv.wait()
                # print("done")

        return [t.result for t in tasks]


# ----------- Serial -------------

class Serial(Task):
    ''' execute tasks in serial '''

    def __init__(self, *tasks):
        super().__init__()
        self._tasks = _flatten(tasks, Serial)


@runtask(Serial)
class _SerialJob(Job):
    ''' execute task in serial '''

    def __call__(self):
        super().__call__()

        tasks = self._task._tasks

        total = len(tasks)
        self._task.progress = 0

        if total > 0:
            count = 0
            for i in tasks:
                i.run(wait=True)
                count += 1
                self._task.progress = count / total

        return [t.result for t in tasks]


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

        self._total = self._task.total
        self._count = 0

    def cancel(self):
        ''' cancel a job '''
        self._stop = True
        super().cancel()

    def task_done_callback(self, task):  # pylint: disable=unused-argument
        ''' called when task is done '''
        with self._cv:
            self._task.decimate_pre_task(task)
            self._count += 1
            self._cv.notify()

    def __call__(self):
        super().__call__()

        bkt = self._task

        while not self._stop:
            with self._cv:
                self._cv.wait(_BucketJob.MAX_WAIT_SECONDS)

                if self._stop:
                    break

                self._task.progress = self._count / self._total

                if bkt.total == 0:  # empty, done.
                    break

                tasks = bkt.find_leaf_tasks()
                if tasks:
                    bkt.remove_tasks(tasks)
                    for i in tasks:
                        i.add_done_callback(self.task_done_callback)
                        i.run(wait=False)

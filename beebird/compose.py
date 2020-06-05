""" Task Composition

    task can be executed in parallel, in serial order or even combined;
    task may be skipped at runtime under some conditions;
    task can be repeated, delayed;

    This module implements the building blocks to compose tasks into a single task.

"""

import threading

from beebird.task import Task
from beebird.job import runtask, Job


def _flatten(tasks, cls):
    ''' flatten the nesting serial/parallel tasks '''
    result = []
    for i in tasks:
        if isinstance(i, cls):
            result.extend(i._tasks) # pylint: disable=protected-access
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

    def task_done_callback(self, task): # pylint: disable=unused-argument
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
            i.addDoneCallback(self.task_done_callback)
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

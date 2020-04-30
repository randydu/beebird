''' Execution Engine for all tasks '''

from py_singleton import singleton

from concurrent import futures

@singleton
class Runner(object):
    """ task executor 

        Singleton class
    """

    def __init__(self):
        self._executor = futures.ThreadPoolExecutor(max_workers=2)
        self._mapJob = {}

    def registerJob(self, clsTask, clsJob):
        if clsTask in self._mapJob:
            raise ValueError(f"Duplicated job registration, task: {clsTask.__name__}")
        self._mapJob[clsTask] = clsJob

    def submitJob(self, job):
        return self._executor.submit(job)

    def runTask(self, tsk, wait = True):
        """ runs a task, returns when the task is done """
        try:
            cls_job = self._mapJob[type(tsk)]
        except KeyError:
            raise ValueError(f"task type ({type(tsk).__name__}) not supported!")
        else:
            return cls_job(tsk).execute(wait)
    
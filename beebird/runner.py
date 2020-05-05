''' Execution Engine for all tasks '''

from py_singleton import singleton

from concurrent import futures

@singleton
class _Runner(object):
    """ task executor """

    def __init__(self):
        self._executor = futures.ThreadPoolExecutor(max_workers=4)

    def submitJob(self, job):
        return self._executor.submit(job)
    
# public 

def submitJob(job):
    return _Runner.instance().submitJob(job)
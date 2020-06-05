''' Execution Engine for all tasks '''

from concurrent import futures

from py_singleton import singleton


@singleton
class _Runner: # pylint: disable=too-few-public-methods
    """ job executor """

    def __init__(self):
        self._executor = futures.ThreadPoolExecutor(max_workers=6)

    def submit(self, job):
        ''' submit a job to be executed by thread pool '''
        return self._executor.submit(job)

# public
def submit_job(job):
    ''' submit a job for execution '''
    return _Runner.instance().submit(job) # pylint: disable=no-member

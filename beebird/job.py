'''
  Job: task is doc, job is to run / control a task at runtime.

'''

from concurrent import futures

from . import runner


class Job:
    ''' Unit to execute a task '''
    def __init__(self, task):
        self._task = task
        self._future = None

    def __call__(self):
        ''' job being executed

            sub-class must call super().__call__(self) first
        '''
        self._task.on_running()

    def cancel(self):
        ''' cancel a job '''
        return self._future.cancel()

    def execute(self, wait=True):
        ''' starts job execution '''
        self._task.on_submitted()
        self._future = runner.submit_job(self)
        self._future.add_done_callback(self._callback_done)
        return self._future.result() if wait else None

    def _callback_done(self, future):
        ''' callback when job is done '''
        try:
            self._task.on_success(future.result())
        except futures.CancelledError:
            self._task.on_cancelled()
        except Exception as ex: # pylint: disable=broad-except
            self._task.on_error(ex)


class CallableTaskJob(Job):
    ''' Job to deal with callable task

        It is the default job class if no other Job class is specified for
        a task class via @runtask
    '''

    def __call__(self):
        super().__call__()
        return self._task()

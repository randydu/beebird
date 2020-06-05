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
        self._task.onRunning()

    def cancel(self):
        ''' cancel a job '''
        return self._future.cancel()

    def execute(self, wait=True):
        ''' starts job execution '''
        self._task.onSubmitted()
        self._future = runner.submit_job(self)
        self._future.add_done_callback(self._callback_done)
        return self._future.result() if wait else None

    def _callback_done(self, future):
        ''' callback when job is done '''
        try:
            self._task.onSuccess(future.result())
        except futures.CancelledError:
            self._task.onCancelled()
        except Exception as ex: # pylint: disable=broad-except
            self._task.onError(ex)


class _CallableTaskJob(Job):
    ''' Job to deal with callable task

        It is the default job class if no other Job class is specified for
        a task class via @runtask
    '''

    def __call__(self):
        super().__call__()
        return self._task()


class runtask: # pylint: disable=(invalid-name, too-few-public-methods)
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
        self._cls_task.setJobClass(cls_job)
        return cls_job


def job(cls_task):
    """ function decorator to turn a function into a job class

    @job(cls_task)
    def upload(task):
        ...

    """

    def wrapper(func):
        class WrapJob(Job):
            ''' job class to run task via decorated function '''
            def __call__(self):
                super().__call__()
                func(self._task)

        cls_task.setJobClass(WrapJob)

    return wrapper

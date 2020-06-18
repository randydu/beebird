'''
  Job: task is doc, job is to run / control a task at runtime.

'''
from concurrent import futures

from . import runner

# name of parameter transferring job to wrapped task function
# if a task func wants to access job instance, it should add '_job' to
# its parameter list
JOB_PARAM = '_job_'

class JobError(Exception):
    ''' base of error from job object '''

class JobStopError(JobError):
    ''' Job is terminated due to itself or some of its sub-jobs are stopped. '''


class Job:
    ''' Unit to execute a task '''
    def __init__(self, tsk):
        self._task = tsk
        self._future = None
        self._stop = False # signal that the running job should be stopped asap.

    @property
    def task(self):
        ''' task to be executed by this job '''
        return self._task

    def __call__(self):
        ''' job being executed

            sub-class must call super().__call__(self) first
        '''
        self._task.on_running()

    def stop(self):
        ''' stop a job

        If the job is already submitted, try to cancel its execution later.
        If the job is being executed, it is the job's responsibility to check
        the "self._stop" signal and terminate the job execution as soon as
        possible by raising a JobStopError.

        returns: True if job is cancelled successfully, False if the job
          cannot be cancelled and has to be stopped by the job itself while
          executing.
        '''
        self._stop = True
        return self._future.cancel()

    def check_stop(self):
        ''' check stop signal, raise JobStopError on stopping '''
        if self._stop:
            raise JobStopError()

    def execute(self, wait=True):
        ''' starts job execution

            returns:
                task result if sync (wait==True) else job itself
        '''
        self._task.on_submitted()
        self._future = runner.submit_job(self)
        self._future.add_done_callback(self._callback_done)
        return self._future.result() if wait else self

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

        e.g.

            @task
            class A:
                def __call__(self, [_job_]):
                    pass
    '''
    def __call__(self):
        super().__call__()
        return self._task.call(_job_=self)

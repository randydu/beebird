''' 
  Job: task is doc, job is to run / control a task at runtime.

''' 

from . import runner

from concurrent import futures

class Job:
    def __init__(self, task):
        self._task = task
        self._future = None

    def __call__(self):
        ''' job being executed 
        
            sub-class must call super().__call__(self) first
        '''
        self._task.onRunning()
    
    def cancel(self):
        return self._future.cancel()

    def execute(self, wait = True):
        self._task.onSubmitted()
        self._future = runner.submitJob(self)
        self._future.add_done_callback(self._cbDone)
        return self._future.result() if wait else None 

    def _cbDone(self, ft): 
        try:
            self._task.onSuccess(ft.result())
        except futures.CancelledError:
            self._task.onCancelled()
        except Exception as e:
            self._task.onError(e)


class _CallableTaskJob(Job):
    ''' Job to deal with callable task 
        
        It is the default job class if no other Job class is specified for a task class via @runtask
    '''
    def __call__(self):
        super().__call__()
        return self._task()
    
class runtask(object):
    """ class decorator to specify which task type to associate 
    
    ex:  
         
         @runtask(MultiFilesCopy)
         @runtask(SingleFileCopy)
         class FileCopyJob(Job):
             def __call__(self):
                 pass

    """
    def __init__(self, clsTask):
        self._clsTask = clsTask

    def __call__(self, clsJob):
        self._clsTask.setJobClass(clsJob)
        return clsJob


def job(clsTask):
    """ function decorator to turn a function into a job class 
    
    @job(clsTask)
    def upload(task):
        ...
    
    """
    
    def toDecorate(f):
        class WrapJob(Job):
            def __call__(self):
                super().__call__()
                f(self._task)
    
        clsTask.setJobClass(WrapJob)


    return toDecorate

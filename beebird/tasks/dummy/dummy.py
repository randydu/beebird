
from beebird.task import task
from beebird.job import job

@task
class DummyTask:
    ''' dummy task for test '''
    pass

@job(DummyTask)
def _(task):
    from time import sleep

    total = 5
    for i in range(total):
        sleep(1)
        task.progress = (i+1)/total


def _register():
    from beebird.cmd import registerCmd
    registerCmd('dummy')

_register()

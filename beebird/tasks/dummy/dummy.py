
from beebird.task import task
from beebird.job import job

@task
class Dummy:
    ''' dummy task for test '''
    pass

@job(Dummy)
def _(task):
    from time import sleep

    print("Dummy >> waiting...")

    total = 5
    for i in range(total):
        sleep(1)
        task.progress = (i+1)/total
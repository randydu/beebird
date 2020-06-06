''' dummy task '''

from time import sleep

from beebird.decorators import task, job



@task
class Dummy: # pylint: disable=too-few-public-methods
    ''' dummy task for test '''


@job(Dummy)
def _(tsk):
    print("Dummy >> waiting...")

    total = 5
    for i in range(total):
        sleep(1)
        tsk.progress = (i+1)/total

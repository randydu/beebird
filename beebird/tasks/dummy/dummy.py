''' dummy task '''

from time import sleep

from beebird.task import task
from beebird.job import job



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

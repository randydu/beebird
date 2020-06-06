''' internal tasks '''

from beebird.task import Task
from beebird.decorators import task


@task
def file(filename: str):
    ''' run a task file '''
    try:
        tsk = Task.loadFromFile(filename)
        return tsk.run()
    except Exception as ex: # pylint: disable=broad-except
        print(ex)

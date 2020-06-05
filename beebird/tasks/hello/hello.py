''' Hello task '''

from beebird.task import task
from beebird.job import job


@task
class Hello: # pylint: disable=too-few-public-methods
    ''' Classical Hello World

        Parameter:

          who: whom to say hello
    '''
    who = "World"


@job(Hello)
def say_hello(tsk):
    ''' job to execute hello task '''
    print("task:\n", tsk.to_json())
    print(f"Hello, {tsk.who}!")

import beebird

from beebird.task import task
from beebird.job import job

beebird.registerCmd('hello')


@task
class Hello:
    ''' dummy task for test '''
    who = "World"

@job(Hello)
def sayHello(task):
    print("task:\n", task.to_json())
    print(f"Hello, {task.who}!")


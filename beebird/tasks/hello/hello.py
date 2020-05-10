from beebird.task import task
from beebird.job import job

@task
class Hello:
    ''' Classical Hello World 
    
        Parameter:

          who: whom to say hello
    '''
    who = "World"

@job(Hello)
def sayHello(task):
    print("task:\n", task.to_json())
    print(f"Hello, {task.who}!")


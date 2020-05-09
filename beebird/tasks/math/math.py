from beebird.task import task

@task
def Add(a:float, b:float):
    print('a: ',a, 'b: ',b)
    return a + b
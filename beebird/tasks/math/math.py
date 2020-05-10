from beebird.task import task

@task
def Add(a:float, b:float):
    """ Adds number a and b """
    print('a: ',a, 'b: ',b)
    return a + b
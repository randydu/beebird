from beebird.task import task

@task
def Add(a:int, b:int = 1):
    """ Adds number a and b """
    print('a: ',a, 'b: ',b)
    return a + b
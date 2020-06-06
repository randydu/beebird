''' math test task '''

from beebird.decorators import task


@task
def add(a: int, b: int = 1): # pylint: disable=invalid-name
    """ Adds number a and b """
    print('a: ', a, 'b: ', b)
    return a + b

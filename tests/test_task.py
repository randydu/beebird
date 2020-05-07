from beebird.task import Task, task_, task, TaskMan

def test_task_create():
    tsk = Task()
    assert tsk.status == Task.Status.INIT


def test_task_decorator(): 
    import pytest

    # private task class
    @task_
    class SayHello(object):
        def __call__(self):
            return "Hello!"

    with pytest.raises(Exception):
        # cannot resolve task by name for a private task
        TaskMan.instance().getTaskByName('SayHello')

    assert SayHello().run() == "Hello!"


    # private task function
    @task_
    def SayHello(): 
        return "Hello!"
    
    with pytest.raises(Exception):
        # cannot resolve task by name for a private task
        TaskMan.instance().getTaskByName('SayHello')

    assert SayHello().run() == "Hello!"
    

    # public task class
    @task
    class SayHello(object):
        def __call__(self):
            return "Hello!"

    assert TaskMan.instance().getTaskByName('SayHello') == SayHello

    # public task function
    @task
    def Hey(object):
        return "Hey!"

    assert TaskMan.instance().getTaskByName('Hey') == Hey


def test_serial(): 
    @task_
    def F(i): 
        print(f"\n>> {i}")
        return i

    g = None
    for x in range(5):
        f = F()
        f.i = x

        g = f if g is None else g*f

    g.run()
   
    print(g.result)
    assert g.result == [*range(5)]


def test_parallel(): 
    import time

    @task_
    def F(i): 
        time.sleep(3)
        print(f"\n>> {i}")
        return i

    # Parallel
    g = None
    for x in range(5):
        f = F()
        f.i = x

        g = f if g is None else g+f

    g.run()
   
    print(g.result)
    assert g.result == [*range(5)]


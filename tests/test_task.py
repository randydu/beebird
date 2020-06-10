import pytest

from beebird.task import Task, TaskMan 
from beebird.decorators import task, task_
from beebird.compose import unity

def test_task_create():
    tsk = Task()
    assert tsk.status == Task.Status.INIT


def test_task_decorator(): 

    # private task class
    @task_
    class SayHello(object):
        def __call__(self):
            return "Hello!"

    with pytest.raises(Exception):
        # cannot resolve task by name for a private task
        TaskMan.instance().find('SayHello')

    assert SayHello().run() == "Hello!"


    # private task function
    @task_
    def SayHello(): 
        return "Hello!"
    
    with pytest.raises(Exception):
        # cannot resolve task by name for a private task
        TaskMan.instance().find('SayHello')

    assert SayHello().run() == "Hello!"
    

    # public task class
    @task
    class SayHello(object):
        def __call__(self):
            return "Hello!"

    assert TaskMan.instance().find('SayHello') == SayHello

    # public task function
    @task
    def Hey(object):
        return "Hey!"

    assert TaskMan.instance().find('Hey') == Hey


def test_serial(): 
    @task_
    def F(i): 
        import time
        time.sleep(1)
        print(f"\n>> {i}")
        return i

    g = unity
    for x in range(5):
        g = g*F(x) 

    g.run()
   
    print(g.result)
    assert g.result == [*range(5)]


def test_parallel(): 

    @task_
    def F(i): 
        import time
        time.sleep(3)
        print(f"\n>> {i}")
        return i

    # Parallel
    g = unity
    for x in range(5):
        g = g + F(x)

    g.run()
   
    print(g.result)
    assert g.result == [*range(5)]

def test_unity(): 
    @task_
    def Dummy():pass

    dummy = Dummy()

    assert dummy + unity == dummy
    assert unity + dummy == dummy
    assert unity + unity == unity

    assert dummy * unity == dummy
    assert unity * dummy == dummy
    assert unity * unity == unity

    unity.run()

    assert unity.result == None

def test_task_init(): 
    import beebird.task
    
    @task_
    def F(a,b): pass

    f0 = F(1)
    assert f0.a == 1    
    assert f0.b == beebird.decorators.empty 


    f1 = F(1,2)
    assert f1.a == 1
    assert f1.b == 2

    f2 = F(a=1,b=2)
    assert f2.a == 1
    assert f2.b == 2

    f3 = F(1,b=2)
    assert f3.a == 1
    assert f3.b == 2
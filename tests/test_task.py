from beebird.task import Task, task_, task, TaskMan, unity

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
        import time
        time.sleep(1)
        print(f"\n>> {i}")
        return i

    g = unity
    for x in range(5):
        f = F()
        f.i = x

        g = g*f 

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
        f = F()
        f.i = x

        g = g + f

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
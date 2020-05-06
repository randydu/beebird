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

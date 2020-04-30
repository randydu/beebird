from beebird.task import Task

def test_task_create():
    tsk = Task()
    assert tsk.status == Task.Status.INIT



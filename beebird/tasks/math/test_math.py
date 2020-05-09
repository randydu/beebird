from beebird.task import Task

def test_add():
    jstr = '{ "_clsid_": "Add", "a": 1, "b": 2 }'
    task = Task.from_json(jstr)

    assert isinstance(task, Task)
    assert type(task).__name__ == 'Add'

    task.run()

    assert task.result == 1+2
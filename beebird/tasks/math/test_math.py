''' test math task '''

from beebird.task import Task

def test_add():
    ''' test add task '''
    jstr = '{ "_CLSID_": "add", "a": 1, "b": 2 }'
    task = Task.from_json(jstr)

    assert isinstance(task, Task)
    assert type(task).__name__ == 'add'

    task.run()

    assert task.result == 1+2

from . import dummy


def test_dummy():
    tsk = dummy.DummyTask()
    jstr = tsk.to_json()
    print(jstr)
    
    tsk1 = dummy.DummyTask.from_json(jstr)
    
    tsk1.run()
    assert tsk1.status == dummy.DummyTask.Status.DONE

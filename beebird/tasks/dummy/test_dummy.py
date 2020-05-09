from . import dummy


def test_dummy():
    tsk = dummy.Dummy()
    jstr = tsk.to_json()
    print(jstr)
    
    tsk1 = dummy.Dummy.from_json(jstr)
    
    tsk1.run()
    assert tsk1.status == dummy.Dummy.Status.DONE

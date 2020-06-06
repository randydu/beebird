''' test dummy task '''

from .dummy import Dummy


def test_dummy():
    ''' test running dummy task '''
    tsk = Dummy()
    jstr = tsk.to_json() # pylint: disable=no-member
    print(jstr)

    tsk1 = Dummy.from_json(jstr) # pylint: disable=no-member

    tsk1.run()
    assert tsk1.status == Dummy.Status.DONE # pylint: disable=no-member

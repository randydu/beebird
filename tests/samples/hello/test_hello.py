''' pytest hello task '''

from beebird.task import Task
from .hello import Hello


def test_hello():
    ''' basic test '''
    tsk = Hello()
    tsk.run()# pylint: disable=no-member


def test_hello_from_json():
    ''' test json serialize of task '''
    tsk = Task.from_json(
        """
        {
            "_CLSID_": "Hello",
            "who": "Randy"
        }"""
    )
    assert tsk.who == "Randy"
    tsk.run()

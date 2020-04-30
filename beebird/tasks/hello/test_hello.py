
from .hello import Hello
from beebird.task import Task


def test_hello():
    tsk = Hello()
    tsk.run()

def test_hello_from_json():
    tsk = Task.from_json(
        """
        {
            "_clsid_": "Hello",
            "who": "Randy"
        }"""
        )
    assert tsk.who == "Randy"
    tsk.run()
    

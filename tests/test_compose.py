from beebird import compose

from beebird.task import task

def test_parallel():

    @task
    def T1(): return 1

    @task
    def T2(): return 2
    
    @task
    def T3(): return 3

    tsk = compose.Parallel([T1(), T2(), T3()])
    tsk.run()

    assert tsk.result == [1, 2, 3]
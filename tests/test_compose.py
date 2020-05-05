from beebird import compose

from beebird.task import task

def test_parallel():

    @task
    def P1(): return 1

    @task
    def P2(): return 2
    
    @task
    def P3(): return 3

    tsk = compose.Parallel([P1(), P2(), P3()])
    tsk.run()

    assert tsk.result == [1, 2, 3]

def test_serial():

    @task
    def S1(): return 1

    @task
    def S2(): return 2
    
    @task
    def S3(): return 3

    tsk = compose.Serial([S1(), S2(), S3()])
    tsk.run()

    assert tsk.result == [1, 2, 3]
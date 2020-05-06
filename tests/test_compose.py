from beebird import compose

from beebird.task import task

def test_parallel():

    @task
    def P1(): return 1

    @task
    def P2(): return 2
    
    @task
    def P3(): return 3

    tsk = compose.Parallel(P1(), P2(), P3())
    tsk.run()

    assert tsk.result == [1, 2, 3]

def test_serial():

    @task
    def S1(): return 1

    @task
    def S2(): return 2
    
    @task
    def S3(): return 3

    tsk = compose.Serial(S1(), S2(), S3())
    tsk.run()

    assert tsk.result == [1, 2, 3]

def test_serial_flatten():

    @task
    def S1(): return 1

    @task
    def S2(): return 2
    
    @task
    def S3(): return 3

    @task
    def S4(): return 4

    tsk = compose.Serial(S1(), compose.Serial(S2(), S3()))
    tsk.run()
    assert tsk.result == [1, [2, 3]]

    tsk.flatten()
    tsk.run()

    assert tsk.result == [1, 2, 3]



def test_mixed(): 
    @task
    def MP1(): return 'mp1'

    @task
    def MP2(): return 'mp2'
    
    @task
    def MS1(): return 'ms1'

    @task
    def MS2(): return 'ms2'

    tsk = compose.Serial( MS1(), compose.Parallel(MP1(), MP2()), MS2() )
    tsk.run()

    assert tsk.result == ['ms1', ['mp1', 'mp2'], 'ms2']

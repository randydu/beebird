from beebird import compose

from beebird.task import Task
from beebird.decorators import task, task_ as ptask 

def test_parallel():

    @ptask
    def P1(): return 1

    @ptask
    def P2(): return 2
    
    @ptask
    def P3(): return 3

    tsk = compose.Parallel(P1(), P2(), P3())
    tsk.run()

    assert tsk.result == [1, 2, 3]
    assert tsk.errcode == Task.ErrorCode.SUCCESS

def test_serial():

    @ptask
    def S1(): return 1

    @ptask
    def S2(): return 2
    
    @ptask
    def S3(): return 3

    tsk = compose.Serial(S1(), S2(), S3())
    tsk.run()

    assert tsk.result == [1, 2, 3]
    assert tsk.errcode == Task.ErrorCode.SUCCESS

def test_serial_flatten():

    @ptask
    def S1(): return 1

    @ptask
    def S2(): return 2
    
    @ptask
    def S3(): return 3

    @ptask
    def S4(): return 4

    tsk = compose.Serial(S1(), compose.Serial(S2(), S3()))
    tsk.run()

    assert tsk.result == [1, 2, 3]
    assert tsk.errcode == Task.ErrorCode.SUCCESS



def test_mixed(): 
    @ptask
    def MP1(): return 'mp1'

    @ptask
    def MP2(): return 'mp2'
    
    @ptask
    def MS1(): return 'ms1'

    @ptask
    def MS2(): return 'ms2'

    tsk = compose.Serial( MS1(), compose.Parallel(MP1(), MP2()), MS2() )
    tsk.run()

    assert tsk.result == ['ms1', ['mp1', 'mp2'], 'ms2']
    assert tsk.errcode == Task.ErrorCode.SUCCESS

import pytest
import time

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

    tsk = compose.Parallel(P1, P2, P3)
    tsk.run()

    assert tsk.result == [1, 2, 3]
    assert tsk.error_code == Task.ErrorCode.SUCCESS

    @ptask
    def err():
        raise ValueError('err')

    tsk = compose.Parallel(P1, P2, P3, err)
    with pytest.raises(ValueError):
        r = tsk.run(wait=True)
        assert tsk.error_code == Task.ErrorCode.ERROR
        assert isinstance(tsk.error, ValueError)


def test_serial():

    @ptask
    def S1(): return 1

    @ptask
    def S2(): return 2
    
    @ptask
    def S3(): return 3

    tsk = compose.Serial(S1, S2, S3)
    tsk.run()

    assert tsk.result == [1, 2, 3]
    assert tsk.error_code == Task.ErrorCode.SUCCESS

    @ptask
    def err():
        raise ValueError('err')

    tsk = compose.Serial(S1, err, S2, S3)
    with pytest.raises(ValueError):
        r = tsk.run(wait=True)
        assert tsk.error_code == Task.ErrorCode.ERROR
        assert isinstance(tsk.error, ValueError)

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
    assert tsk.error_code == Task.ErrorCode.SUCCESS



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
    assert tsk.error_code == Task.ErrorCode.SUCCESS


def test_do():
    @ptask
    def ok():
        return 'ok' 
    
    r = compose.do(ok).run(wait=True)
    assert r == 'ok'

    @ptask
    def then1():
        return 'good'
    
    r = compose.do(ok).then(then1).run(wait=True)
    assert r == ['ok', 'good']

    @ptask
    def err():
        raise ValueError('err')
    
    tsk = compose.do(ok).then(err)
    with pytest.raises(ValueError):
        r = tsk.run(wait=True)
        assert tsk.error_code == Task.ErrorCode.ERROR
        assert r is None

    @ptask
    def err_handler(err):
        return str(err)
    
    r = compose.do(ok).then(err).catch(err_handler).run(wait=True)
    assert r == 'err'

tries = 0
def test_tryrun():
    global tries
    
    @ptask
    def f():
        ''' success on second tries '''
        global tries
        tries += 1
        print('tries: ', tries)
        if tries < 2:
            raise ValueError()
        return 'ok'
    
    tries = 0
    with pytest.raises(ValueError):
        tsk = compose.TryRun(f)
        assert tsk.run(wait=True) == 'ok'

    tries = 0
    with pytest.raises(ValueError):
        tsk = compose.TryRun(f, max_tries=1, sleep_seconds=0)
        tsk.run(wait=True)
        assert tsk.error_code == Task.ErrorCode.ERROR


fifo_done = False
def test_fifo():
    @ptask
    def f(i):
        global fifo_done
        time.sleep(1)
        print(f'>> {i}')
        fifo_done = (i == 9)
    
    fifo = compose.FIFO(1)
    fifo_job = fifo.run(wait=False)

    for i in range(10):
        print(f'submitting job {i}')
        ok = False
        while not ok:
            ok = fifo.add(f(i))
        print(f'job {i} submited')

    while not fifo_done:
        time.sleep(1)

    fifo_job.stop()

    print('waiting for fifo stopped...')
    while fifo.status != Task.Status.DONE:
        time.sleep(1)
        print(f'fifo status: {fifo.status}')

    
''' test task schedule '''
import sys
import pytest
from time import sleep

from beebird.decorators import task
from beebird.compose import *


def test_add():
    ''' test add method '''
    bkt = Bucket()

    ta = Task()
    tb = Task()
    tc = Task()

    bkt.add(ta, [tb])
    bkt.add(tb, [tc])
    bkt.add(tc)  # unnecessary but ok


def test_leaf_tasks():
    ''' test find_leaf_tasks() '''
    bkt = Bucket()

    ta = Task()
    bkt.add(ta)
    assert bkt.find_leaf_tasks() == [ta]

    bkt.clear()
    tb = Task()
    bkt.add(tb, [ta])
    assert bkt.find_leaf_tasks() == [ta]

    bkt.clear()
    bkt.add(ta, [ta])
    assert bkt.find_leaf_tasks() == []


def test_loopcheck():
    ''' test loopback checking '''
    bkt = Bucket()

    ta = Task()

    bkt.add(ta, [ta])
    assert bkt.find_loop()
    bkt.clear()

    tb = Task()
    bkt.add(ta, [tb])
    bkt.add(tb, [ta])
    assert bkt.find_loop()
    bkt.clear()

    tc = Task()
    bkt.add(ta, [tb, tc])
    bkt.add(tc, [ta])
    assert bkt.find_loop()
    bkt.clear()

    bkt.add(ta, [tb])
    bkt.add(tb, [tc])
    bkt.add(tc, [ta])
    assert bkt.find_loop()


def test_bucket_run():
    ''' test bucket running order '''
    results = []

    @task
    def echo(i):
        print('echo: %d' % i)
        sleep(1)
        results.append(i)

    t0 = echo(0)
    t1 = echo(1)
    t2 = echo(2)
    t3 = echo(3)

    bkt = Bucket()

    # order 0: t0->[t1|t2]-> t3
    bkt.add(t1, [t0])
    bkt.add(t2, [t0])
    bkt.add(t3, [t0, t1, t2])

    bkt.run(wait=True)
    print(results)
    assert results in [[0, 1, 2, 3], [0, 2, 1, 3]]

    # order 1: [t0|t1]->[t2|t3]
    bkt.clear()
    results = []

    bkt.add(t2, [t0, t1])
    bkt.add(t3, [t0, t1])

    bkt.run(wait=True)
    print(results)
    assert results in [[0, 1, 2, 3], [1, 0, 2, 3], [0, 1, 3, 2], [1, 0, 3, 2]]

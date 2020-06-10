''' test task schedule '''
import sys
import pytest

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

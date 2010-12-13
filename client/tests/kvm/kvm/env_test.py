#!/usr/bin/env python
"""Unit tests for the kvm.env module

@author: Eduardo Habkost <ehabkost@redhat.com>
"""
import unittest

import kvm.env

class KvmEnvtest(unittest.TestCase):
    def test_get(self):
        d = {'a':100}
        e = kvm.env.KvmEnv(d)
        self.assertEquals(e['a'], 100)

    def test_set(self):
        e = kvm.env.KvmEnv({})
        e['x'] = 42
        self.assertEquals(e['x'], 42)
        self.assertEquals(e.data['x'], 42)

    def test_identity(self):
        # make sure references are kept when setting items:
        e = kvm.env.KvmEnv({})

        l = [1,2,3]
        e['x'] = l
        self.assertIs(e['x'], l)
        self.assertIs(e.data['x'], l)

    def test_str(self):
        # make sure str(env) works like the dictionary version

        d = {'x':1, 'y':2}
        e = kvm.env.KvmEnv(d)

        self.assertEquals(str(d), str(e))

    def test_del(self):
        d = {'parrot':'alive'}
        e = kvm.env.KvmEnv(d)

        del e['parrot']
        self.assertRaises(KeyError, lambda: e['parrot'])
        self.assertRaises(KeyError, lambda: e.data['parrot'])

    def test_get(self):
        d = {'foo':'bar'}
        e = kvm.env.KvmEnv(d)
        self.assertEquals(e.get('foo', 'x'), 'bar')
        self.assertEquals(e.get('bar', 'baz'), 'baz')
        self.assertIs(e.get('bar'), None)

    def test_in(self):
        d = {'foo':'bar'}
        e = kvm.env.KvmEnv(d)
        self.assertTrue('foo' in e)
        self.assertFalse('not-here' in e)

    def test_keys(self):
        d = {'foo':'bar', 'foo2':'bar2'}
        e = kvm.env.KvmEnv(d)
        self.assertEquals(set(e.keys()), set(['foo', 'foo2']))

    def test_values(self):
        d = {'foo':'bar', 'foo2':'bar2'}
        e = kvm.env.KvmEnv(d)
        self.assertEquals(set(e.values()), set(['bar', 'bar2']))

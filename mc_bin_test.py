#!/usr/bin/env python

# This test requires a memcached server to be running on localhost and
# my mc_bin_client library.

import time

import testgen
from testgen import Condition, Effect, Action, Driver

import mc_bin_client

EXPTIME = 2

######################################################################
# Conditions
######################################################################

class ExistsCondition(Condition):

    def __call__(self, k, state):
        return k in state[1]

class DoesNotExistCondition(Condition):

    def __call__(self, k, state):
        return k not in state[1]

######################################################################
# Effects
######################################################################

class StoreEffect(Effect):

    def __init__(self, v='0', method='set'):
        self.v = v
        self.method = method

    def __call__(self, k, state):
        state[1][k] = self.v
        getattr(state[0], self.method)(k, EXPTIME, 0, self.v)

class DeleteEffect(Effect):

    def __call__(self, k, state):
        del state[1][k]
        state[0].delete(k)

class DelayEffect(Effect):

    def __call__(self, k, state):
        state[1].clear()
        time.sleep(EXPTIME+1)

class AppendEffect(Effect):

    suffix = '-suffix'

    def __call__(self, k, state):
        state[1][k] = state[1][k] + self.suffix
        state[0].set(k, EXPTIME, 0, state[1][k])

class PrependEffect(Effect):

    prefix = 'prefix-'

    def __call__(self, k, state):
        state[1][k] = self.prefix + state[1][k]
        state[0].set(k, EXPTIME, 0, state[1][k])

######################################################################
# Actions
######################################################################

class Set(Action):

    preconditions = []
    effect = StoreEffect()
    postconditions = [ExistsCondition()]

class Add(Action):

    preconditions = [DoesNotExistCondition()]
    effect = StoreEffect('0', 'add')
    postconditions = [ExistsCondition()]

class Delete(Action):

    preconditions = [ExistsCondition()]
    effect = DeleteEffect()
    postconditions = [DoesNotExistCondition()]

class Append(Action):

    preconditions = [ExistsCondition()]
    effect = AppendEffect()
    preconditions = [ExistsCondition()]

class Delay(Action):

    effect = DelayEffect()

class Prepend(Action):

    preconditions = [ExistsCondition()]
    effect = PrependEffect()
    preconditions = [ExistsCondition()]

######################################################################
# Driver
######################################################################

class MCDriver(Driver):

    def newState(self):
        self.state = [mc_bin_client.MemcachedClient(), {}]
        self.state[0].flush()
        return self.state

    def startSequence(self, seq):
        print "Running", ', '.join(a.name for a in seq)

    def endSequence(self, seq, k, state):
        value = state[1].get(k, None)
        try:
            inState = self.state[0].get(k)[-1]
        except:
            inState = None

        print ['FAIL', 'PASS'][value == inState]

if __name__ == '__main__':
    testgen.runTest(testgen.findActions(globals().values()),
                    MCDriver(), 3, 4)

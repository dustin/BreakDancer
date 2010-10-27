#!/usr/bin/env python

import itertools

######################################################################
# Conditions
######################################################################

class Condition(object):
    pass

class ExistsCondition(object):

    def __call__(self, k, state):
        return k in state

class ExistsAsNumber(object):

    def __call__(self, k, state):
        try:
            int(state[k])
            return True
        except:
            return False

class MaybeExistsAsNumber(ExistsAsNumber):

    def __call__(self, k, state):
        return k not in state or ExistsAsNumber.__call__(self, k, state)

class DoesNotExistCondition(object):

    def __call__(self, k, state):
        return k not in state

class NothingExistsCondition(object):

    def __call__(self, k, state):
        return not bool(state)

######################################################################
# Effects
######################################################################

class Effect(object):
    pass

class StoreEffect(Effect):

    def __init__(self, v='0'):
        self.v = v

    def __call__(self, k, state):
        state[k] = self.v

class DeleteEffect(Effect):

    def __call__(self, k, state):
        del state[k]

class FlushEffect(Effect):

    def __call__(self, k, state):
        state.clear()

class AppendEffect(Effect):

    suffix = '-suffix'

    def __call__(self, k, state):
        state[k] = state[k] + self.suffix

class PrependEffect(Effect):

    prefix = 'prefix-'

    def __call__(self, k, state):
        state[k] = self.prefix + state[k]

class ArithmeticEffect(Effect):

    default = '0'

    def __init__(self, by=1):
        self.by = by

    def __call__(self, k, state):
        if k in state:
            state[k] = str(max(0, int(state[k]) + self.by))
        else:
            state[k] = self.default

######################################################################
# Actions
######################################################################

class Action(object):

    preconditions = []
    effect = None
    postconditions = []

    key = 'testkey'

    @property
    def name(self):
        n = self.__class__.__name__
        return n[0].lower() + n[1:]

class Set(Action):

    effect = StoreEffect()
    postconditions = [ExistsCondition()]

class Add(Action):

    preconditions = [DoesNotExistCondition()]
    effect = StoreEffect()
    postconditions = [ExistsCondition()]

class Delete(Action):

    preconditions = [ExistsCondition()]
    effect = DeleteEffect()
    postconditions = [DoesNotExistCondition()]

class Flush(Action):

    effect = FlushEffect()
    postconditions = [NothingExistsCondition()]

class Delay(Flush):
    pass

class Append(Action):

    preconditions = [ExistsCondition()]
    effect = AppendEffect()
    preconditions = [ExistsCondition()]

class Prepend(Action):

    preconditions = [ExistsCondition()]
    effect = PrependEffect()
    preconditions = [ExistsCondition()]

class Incr(Action):

    preconditions = [ExistsAsNumber()]
    effect = ArithmeticEffect(1)
    postconditions = [ExistsAsNumber()]

class Decr(Action):

    preconditions = [ExistsAsNumber()]
    effect = ArithmeticEffect(-1)
    postconditions = [ExistsAsNumber()]

class IncrWithDefault(Action):

    preconditions = [MaybeExistsAsNumber()]
    effect = ArithmeticEffect(1)
    postconditions = [ExistsAsNumber()]

class DecrWithDefault(Action):

    preconditions = [MaybeExistsAsNumber()]
    effect = ArithmeticEffect(-1)
    postconditions = [ExistsAsNumber()]

actions = []
for __t in (t for t in globals().values() if isinstance(type, type(t))):
    if Action in __t.__mro__ and __t != Action:
        actions.append(__t)

class Driver(object):

    def preSuite(self, seq):
        pass

    def startSequence(self, seq):
        pass

    def startAction(self, action):
        pass

    def endAction(self, action, value, errored):
        pass

    def endSequence(self, seq):
        pass

    def postSuite(self, seq):
        pass

class EngineTestAppFormatter(Driver):

    def endSequence(self, seq):
        print "}"
        print ""

    def preSuite(self, seq):
        print '#include "suite_stubs.h"'
        print ""

    def testName(self, seq):
        return 'test_' + '_'.join(a.name for a in seq)

    def startSequence(self, seq):
        f = "static enum test_result %s" % self.testName(seq)
        print ("%s(ENGINE_HANDLE *h,\n%sENGINE_HANDLE_V1 *h1) {"
               % (f, " " * (len(f) + 1)))

    def startAction(self, action):
        if isinstance(action, Delay):
            s = "    delay(expiry+1);"
        elif isinstance(action, Flush):
            s = "    flush(h, h1);"
        elif isinstance(action, Delete):
            s = '    del(h, h1);'
        else:
            s = '    %s(h, h1);' % (action.name)
        print s

    def postSuite(self, seq):
        print """MEMCACHED_PUBLIC_API
engine_test_t* get_tests(void) {

    static engine_test_t tests[]  = {
"""
        for seq in sorted(tests):
            print '        {"%s",\n         %s,\n         NULL, teardown, NULL},' % (
                ', '.join(a.name for a in seq),
                self.testName(seq))

        print """        {NULL, NULL, NULL, NULL, NULL}
    };
    return tests;
}"""

    def finalState(self, val):
        if val:
            print '    checkValue(h, h1, "%s");' % val
        else:
            print '    assertNotExists(h, h1);'
        print "    return SUCCESS;"

    def endAction(self, action, value, errored):
        if value:
            vs = ' // value is "%s"' % value
        else:
            vs = ' // value is not defined'

        if errored:
            print "    assertHasError();" + vs
        else:
            print "    assertHasNoError();" + vs

if __name__ == '__main__':
    instances = itertools.chain(*itertools.repeat([a() for a in actions], 3))
    formatter = EngineTestAppFormatter()
    tests = set(itertools.permutations(instances, 4))
    formatter.preSuite(tests)
    k = 'testkey'
    for seq in sorted(tests):
        state = {}
        formatter.startSequence(seq)
        for a in seq:
            formatter.startAction(a)
            haserror = not all(p(k, state) for p in a.preconditions)
            if not haserror:
                a.effect(k, state)
                haserror = not all(p(k, state) for p in a.postconditions)
            formatter.endAction(a, state.get(k), haserror)
        formatter.finalState(state.get(k))
        formatter.endSequence(seq)

    formatter.postSuite(tests)

#!/usr/bin/env python

import itertools

class State(object):

    def __init__(self):
        self.objects = {}
        self.errored = False

    def starting(self):
        self.errored = False

    def set(self, k, v, until=0):
        self.objects[k] = (until, v)

    def delete(self, k, force=False):
        if k not in self.objects:
            if not force:
                self.error()
        else:
            del self.objects[k]

    def add(self, k, v, until=0):
        if k in self.objects:
            self.error()
        else:
            self.set(k, v, until)

    def get(self, k):
        return self.objects.get(k)

    def flush(self, *whatever):
        self.objects = {}

    def error(self):
        self.errored = True

class Action(object):

    key = 'testkey'

    @property
    def name(self):
        n = self.__class__.__name__
        return n[0].lower() + n[1:]

class Set(Action):

    def run(self, state):
        state.set(self.key, '0')

class Add(Action):

    def run(self, state):
        state.add(self.key, '0')

class Delete(Action):

    def run(self, state):
        state.delete(self.key)

class Delay(Action):

    def run(self, state):
        state.delete(self.key, True)

class Flush(Action):

    def run(self, state):
        state.flush()

class Append(Action):

    def run(self, state):
        val = state.get(self.key)
        if val:
            exp, v = val
            try:
                state.set(self.key, self.transform(v), exp)
            except:
                state.error()
        else:
            self.missing(state)

    def missing(self, state):
        state.error()

    def transform(self, v):
        return v + "-suffix"

class Prepend(Append):

    def transform(self, v):
        return "prefix-" + v

class Incr(Append):

    def transform(self, v):
        return str(int(v) + 1)

class Decr(Append):

    def transform(self, v):
        return str(int(v) - 1)

class IncrWithDefault(Incr):

    def missing(self, state):
        state.set(self.key, self.transform('0'))

class DecrWithDefault(IncrWithDefault):
    pass

actions = []
for __t in (t for t in globals().values() if isinstance(type, type(t))):
    if Action in __t.__mro__ and __t != Action:
        actions.append(__t)

class CFormatter(object):

    def finalState(self, val):
        if val:
            s = "exists as %s" % val[1];
        else:
            s = "doesn't exist"
        print "    // final state:  object %s" % s

    def startSequence(self, seq):
        print "void %s() {" % self.testName(seq)

    def endSequence(self, seq):
        print "}"
        print ""

    def startAction(self, action):
        if isinstance(action, Delay):
            print "    delay(expiry+1);"
        elif isinstance(action, Flush):
            print "    flush();"
        else:
            print '    %s();' % (action.name)

    def endAction(self, action, value, errored):
        pass

    def preSuite(self, seq):
        print '#include "testsuite.h"'
        print ""

    def postSuite(self, seq):
        print "int main(int argc, char **argv) {"
        for seq in sorted(tests):
            print "    %s();" % self.testName(seq)
        print "}"

    def testName(self, seq):
        return 'test_' + '_'.join(a.name for a in seq)

class EngineTestAppFormatter(CFormatter):

    def startSequence(self, seq):
        f = "static enum test_result %s" % self.testName(seq)
        print ("%s(ENGINE_HANDLE *h,\n%sENGINE_HANDLE_V1 *h1) {"
               % (f, " " * (len(f) + 1)))

    def startAction(self, action):
        if isinstance(action, Delay):
            s = "    testHarness.time_travel(expiry+1);"
        elif isinstance(action, Flush):
            s = "    flush(h, h1);"
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
            print '    checkValue(h, h1, value, "%s");' % val[1]
        else:
            print '    assertNotExists(h, h1);'

    def endAction(self, action, value, errored):
        if value:
            vs = ' // value is "%s"' % value[1]
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
    for seq in sorted(tests):
        state = State()
        formatter.startSequence(seq)
        for a in seq:
            state.starting()
            formatter.startAction(a)
            a.run(state)
            formatter.endAction(a, state.get(seq[0].key), state.errored)
        formatter.finalState(state.get(seq[0].key))
        formatter.endSequence(seq)

    formatter.postSuite(tests)

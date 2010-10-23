#!/usr/bin/env python

import itertools

class State(object):

    def __init__(self, formatter):
        self.objects = {}
        self.formatter = formatter

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

    def final(self, k):
        self.formatter.finalState(self.objects.get(k))

    def flush(self, *whatever):
        self.objects = {}

    def error(self):
        self.formatter.error()

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

    def error(self):
        print "    // error"

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

    def endAction(self, action):
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

if __name__ == '__main__':
    instances = itertools.chain(*itertools.repeat([a() for a in actions], 3))
    k = "somekey"
    formatter = CFormatter()
    tests = set(itertools.permutations(instances, 4))
    formatter.preSuite(tests)
    for seq in sorted(tests):
        state = State(formatter)
        formatter.startSequence(seq)
        for a in seq:
            formatter.startAction(a)
            a.run(state)
            formatter.endAction(a)
        state.final(seq[0].key)
        formatter.endSequence(seq)

    formatter.postSuite(tests)

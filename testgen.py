#!/usr/bin/env python

import itertools

class State(object):

    def __init__(self):
        self.objects = {}

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
        if k in self.objects:
            s = "exists";
        else:
            s = "doesn't exist";
        print "    // final state:  object %s" % s

    def flush(self, *whatever):
        self.objects = {}

    def error(self):
        print "    // error"

class Action(object):

    @property
    def name(self):
        n = self.__class__.__name__
        return n[0].lower() + n[1:]

    def c_code(self, k, state):
        print '    %s("%s");' % (self.name, k)

class Set(Action):

    def run(self, k, state):
        self.c_code(k, state)
        state.set(k, '0')

class Add(Action):

    def run(self, k, state):
        self.c_code(k, state)
        state.add(k, 'val')

class Delete(Action):

    def run(self, k, state):
        self.c_code(k, state)
        state.delete(k)

class Delay(Action):

    def run(self, k, state):
        print "    // sleep(expiry+1);"
        state.delete(k, True)

class Flush(Action):

    def run(self, k, state):
        self.c_code(k, state)
        state.flush(k, True)

class Append(Action):

    def run(self, k, state):
        self.c_code(k, state)
        val = state.get(k)
        if val:
            exp, v = val
            try:
                state.set(k, self.transform(v), exp)
            except:
                state.error()
        else:
            self.missing(k, state)

    def missing(self, k, state):
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

class IncrWithDefault(Append):
    pass

    def missing(self, k, state):
        state.set(k, self.transform('0'))

class DecrWithDefault(IncrWithDefault):
    pass

actions = []
for __t in (t for t in globals().values() if isinstance(type, type(t))):
    if Action in __t.__mro__ and __t != Action:
        actions.append(__t)

if __name__ == '__main__':
    instances = itertools.chain(*itertools.repeat([a() for a in actions], 3))
    k = "somekey"
    for (i, seq) in enumerate(itertools.permutations(instances, 4)):
        state = State()
        print "// %s" % ', '.join(a.name for a in seq)
        print "void test_%d() {" % i
        for a in seq:
            a.run(k, state)
        state.final(k)
        print "}"
        print ""

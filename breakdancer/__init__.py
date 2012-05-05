#!/usr/bin/env python

import itertools

class Condition(object):
    """Something asserted to be true during the test.

    A given condition may be used as a precondition or a
    postcondition."""

    def __call__(self, k, state):
        """Called with a key and a state.  True if the condition is met."""
        return True

class Effect(object):
    """The affect an action will perform."""

    def __call__(self, k, state):
        """Called with a key and a state.

        The effect modifies the state as appropriate."""

class Action(object):
    """Actions are the operations that will be permuted into test cases.

    Each action has a collection of preconditions and postconditions
    that will be evaluated for checking input and output state for the
    action.

    Action.preconditions is the collection of conditions that must all
    be true upon input to the action.  If any condition is not true,
    the effect is not executed and the action state is considered
    "errored."

    Action.effect is the callable that is expected to alter the state
    to satisfy the postconditions of the action.

    Action.postconditions is the collection of conditions that must
    all be true after the effect of the action completes.
    """

    preconditions = []
    effect = None
    postconditions = []
    enabled = True

    @property
    def name(self):
        """The name of this action (default derived from class name)"""
        n = self.__class__.__name__
        return n[0].lower() + n[1:]

class Driver(object):
    """The driver "performs" the test."""

    def newState(self):
        """Initialize and return the state for a test."""
        return {}

    def preSuite(self, seq):
        """Invoked with the sequence of tests before any are run."""

    def startSequence(self, seq):
        """Invoked with the sequence of actions in a single test
        before it is performed."""

    def startAction(self, action):
        """Invoked when before starting an action."""

    def endAction(self, action, state, errored):
        """Invoked after the action is performed."""

    def endSequence(self, seq, state):
        """Invoked at the end of a sequence of tests."""

    def postSuite(self, seq):
        """Invoked with the sequence of tests after all of them are run."""

def runTest(actions, driver, duplicates=3, length=4):
    """Run a test with the given collection of actions and driver.

    The optional argument `duplicates' specifies how many times a
    given action may be duplicated in a sequence.

    The optional argument `length` specifies how long each test
    sequence is.
    """

    instances = [a() for a in actions]

    tests = set(itertools.product(*itertools.repeat(instances, length)))
    rm = set(s for s in tests if max(s.count(i) for i in set(s)) > duplicates)
    tests -= rm

    driver.preSuite(tests)
    for seq in sorted(tests):
        state = driver.newState()
        driver.startSequence(seq)
        for a in seq:
            driver.startAction(a)
            haserror = not all(p(state) for p in a.preconditions)
            if not haserror:
                try:
                    a.effect(state)
                    haserror = not all(p(state) for p in a.postconditions)
                except:
                    haserror = True
            driver.endAction(a, state, haserror)
        driver.endSequence(seq, state)
    driver.postSuite(tests)

def findActions(classes):
    """Helper function to extract action subclasses from a collection
    of classes."""

    def isEnabledAction(t):
        return (t != Action
                and isinstance(type, type(t))
                and issubclass(t, Action) and t.enabled)

    return [t for t in classes if isEnabledAction(t)]

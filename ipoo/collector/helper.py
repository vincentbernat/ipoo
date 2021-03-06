"""
Various helpers for plugins
"""

import collections
import functools
import time
import socket
import re
import cPickle

from twisted.python import failure
from twisted.internet import task, defer

# Helper functions for handle (from ICollector)
HOSTREGEX = re.compile(r'^(?=.{1,255}$)[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?(?:\.[0-9A-Za-z](?:(?:[0-9A-Za-z]|\b-){0,61}[0-9A-Za-z])?)*\.?$')
def handleFQDN(user_function):
    """Modify handle function to let say that it also handles FQDN"""
    @functools.wraps(user_function)
    def wrapper(self, cfg, query):
        if HOSTREGEX.match(query):
            for domain in cfg.get('domains', []):
                if query.endswith(domain):
                        return True
        return user_function(self, cfg, query)

    return wrapper

def handleIPv4(user_function):
    '''Modify handle function to let say that it also handles IP'''
    @functools.wraps(user_function)
    def wrapper(self, cfg, query):
        try:
            socket.inet_aton(query)
        except:
            return user_function(self, cfg, query)
        else:
            return True

    return wrapper

def handleNetwork(user_function):
    '''Modify handle function to let say it also handles network'''
    @functools.wraps(user_function)
    def wrapper(self, cfg, query):
        s = query.split("/")
        if len(s) == 2:
            net, mask = s
            try:
                socket.inet_aton(net)
                mask = int(mask)
                if mask >= 0 and mask <= 32:
                    return True
            except:
                pass
        return user_function(self, cfg, query)

    return wrapper

def requireCfg(user_function):
    '''Modify handle to require a configuration item'''
    @functools.wraps(user_function)
    def wrapper(self, cfg, query):
        if self.name not in cfg:
            return False
        return user_function(self, cfg, query)

    return wrapper

# Other helper functions
def refresh(period):
    '''
    Recall the function periodically.

    After the decorated function has been called once, it will be
    called again with the same arguments every `period' seconds. Only
    one periodic call is handled per function. If a function is called
    with different arguments, only the last call will be repeated.

    @param period: how many seconds between two calls
    '''
    def decorating_function(user_function):
        d = [] # Deferred is enclosed into a list to be able to keep a
               # reference into the wrapper.

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            while d:
                d.pop().stop()
            result = user_function(*args, **kwds)
            l = task.LoopingCall(lambda: user_function(*args, **kwds))
            l.start(period, now=False)
            d.append(l)
            return result

        return wrapper
    return decorating_function

class CachedDeferred(object):
    '''
    A way to let objects wait for the same deferred. The first one
    create an instance of this class and the other one will register
    themselves. This is better than just adding callback to the
    deferrer since we ensure that its result is not altered by other
    users.
    '''

    def __init__(self, deferred):
        self.deferreds = []
        self.called = False
        self.result = None
        deferred.addBoth(self._callback)

    def _callback(self, result):
        # Our deferred has been trigerred
        self.called = True
        self.result = result
        while self.deferreds:
            d = self.deferreds.pop()
            if isinstance(result, failure.Failure):
                d.errback(result)
            else:
                d.callback(result)

    def register(self):
        if self.called:
            return self.result
        d = defer.Deferred()
        self.deferreds.append(d)
        return d

def cache(maxtime=0, maxsize=100):
    '''
    Least-recently-used cache decorator with time constraints.

    Arguments are matched against their representations! When the
    original function returns a deferred, the cached function may or
    may not return a deferred. The caller should be able to handle
    this case.
    '''
    maxqueue = maxsize * 10
    def decorating_function(user_function):
        cache = {}                  # mapping of args to results
        lastaccess = {}             # time of last access of an item
        creation = {}               # time of creation
        kwd_mark = object()         # separate positional and keyword args

        @functools.wraps(user_function)
        def wrapper(*args, **kwds):
            # cache key records both positional and keyword args
            key = args
            if kwds:
                key += (kwd_mark,) + tuple(sorted(kwds.items()))
            key = repr(key)

            # get cache entry or compute if not found
            t = time.time()
            try:
                # if the entry is expired, try to get a new one
                if maxtime and t - creation[key] > maxtime:
                    del cache[key], lastaccess[key], creation[key]
                    raise KeyError
                result = cache[key]
                # If we the cached data comes from a deferred, we need
                # to register for it.
                if isinstance(result, CachedDeferred):
                    result = result.register()
                lastaccess[key] = t
            except KeyError:
                result = user_function(*args, **kwds)
                cache[key] = result
                lastaccess[key] = t
                creation[key] = t
                # If the result is a deferred, we need to remember its
                # result when it will fire
                if isinstance(result, defer.Deferred):
                    result.addBoth(remember, key)
                    result = CachedDeferred(result)
                    cache[key] = result
                    result = result.register()

                # purge least recently used cache entry, not really
                # performance oriented
                if maxsize and len(cache) > maxsize:
                    items = lastaccess.items()
                    items.sort(key=lambda x: x[1])
                    key = items[0][0]
                    del cache[key], lastaccess[key], creation[key]

            return result

        def remember(x, key):
            if isinstance(x, failure.Failure):
                # We got a failure and we don't cache failures
                try:
                    del cache[key], lastaccess[key], creation[key]
                except KeyError:
                    # Maybe the key has already expired
                    pass
            else:
                # Cache the result directly. We don't need the
                # deferred anymore.
                cache[key] = x
            return x

        return wrapper
    return decorating_function

if __name__ == "__main__":
    from random import choice

    @cache(maxsize=5, maxtime=2)
    def f(x, y):
        return x+y+choice(range(100))

    # First element should stay the same for the 10 iterations, then
    # the value should change and stay constant for the ten remaining
    # iterations
    for i in range(20):
        print "%d: %d, %d" % (i, f(5,6), f(7, choice(range(100))))
        time.sleep(0.2)


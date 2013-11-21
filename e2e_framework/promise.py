"""
Variation on the "promise" design pattern.
Promises make it easier to handle asynchronous operations correctly.

Purists may complain that this does not match the usual meaning of "promise";
see, for example, http://domenic.me/2012/10/14/youre-missing-the-point-of-promises/
I'm using the word "promise" because I couldn't think of a better word
to describe what this class does.
"""
import time
import logging
from contextlib import contextmanager

LOGGER = logging.getLogger(__name__)


class BrokenPromise(Exception):
    """
    The promise was not satisfied within the time constraints.
    """

    def __init__(self, promise):
        """
        `promise` is the `Promise` object that was broken.
        """
        super(BrokenPromise, self).__init__()
        self._promise = promise

    def __str__(self):
        return "Promise not satisfied: {0}".format(self._promise)


class Promise(object):
    """
    Check that an asynchronous action completed, blocking until it does
    or timeout / try limits are reached.
    """

    def __init__(self, check_func, description, try_limit=None, try_interval=0.5, timeout=30):
        """
        Configure the `Promise`.

        `check_func()` is a function that returns a `(is_satisfied, result)` tuple
        where `is_satisfied` is a boolean indicating whether the promise has been satisfied and
        `result` is a value to pass to the `with` block

        The `Promise` will poll `check_func()` until either:
            * The promise is satisfied
            * The promise runs out of tries (checks more than `try_limit` times)
            * The promise runs out of time (takes longer than `timeout` seconds)

        In the second two cases, the promise is "broken" and an exception will be raised.
        `description` is a string that will be included in the exception to make debugging easier.

        Note: `try_limit` and `timeout` can be set to `None` to disable the limit.

        Example:

            # Dummy check function that indicates the promise is always satisfied
            check_func = lambda: (True, "Hello world!")

            # Check up to 5 times if the operation has completed
            promise = Promise(check_func, "Operation has completed", try_limit=5, timeout=None)

            # Ensure that the next operation executes only if the promise is satisfied
            # `result` will be "Hello world!", because that's what `check_func` returned
            # If the promise isn't satisfied, this will throw a `BrokenPromise` exception
            with block_until(promise) as result:

                # This should print "Hello World!"
                print result

            # Alternatively, you can get the result directly:
            print fulfill(promise)
        """
        self._check_func = check_func
        self._description = description
        self._try_limit = try_limit
        self._try_interval = try_interval
        self._timeout = timeout
        self._num_tries = 0

    def __str__(self):
        return str(self._description)

    def check_fulfilled(self):
        """
        Return tuple `(is_fulfilled, result)` where
        `is_fulfilled` is a boolean indicating whether the promise has been fulfilled
        and `result` is the value to pass to the `with` block.
        """
        is_fulfilled = False
        result = None
        start_time = time.time()

        # Check whether the promise has been fulfilled until we run out of time or attempts
        caught_exceptions = dict()
        while self._has_time_left(start_time) and self._has_more_tries():

            is_fulfilled, result = self._check_func()

            # If the promise is satisfied, then continue execution
            if is_fulfilled:
                break

            # Delay between checks
            time.sleep(self._try_interval)

        return is_fulfilled, result

    def _has_time_left(self, start_time):
        """
        Return True if the elapsed time is greater than the timeout.
        If no timeout is set, always return True.
        """
        if self._timeout is None:
            return True
        else:
            return time.time() - start_time < self._timeout

    def _has_more_tries(self):
        """
        Return True if the promise has additional tries.
        If `_try_limit` is `None`, always return True.
        """
        if self._try_limit is None:
            return True
        else:
            self._num_tries += 1
            return self._num_tries < self._try_limit


@contextmanager
def block_until(promise):
    """
    Block execution until the `promise` is fulfilled.
    If not fulfilled, raise a `BrokenPromise` exception.
    """

    is_fulfilled, result = promise.check_fulfilled()

    if is_fulfilled:
        yield result
    else:
        raise BrokenPromise(promise)

@contextmanager
def block_after(promise):
    """
    After the block executes, block until the `promise`
    is fulfilled.  In this case, any output from the
    promise is discarded.
    """

    # Execute the 'with' block
    yield

    # Block until the promise is fulfilled or we time out
    is_fulfilled, _ = promise.check_fulfilled()

    if not is_fulfilled:
        raise BrokenPromise(promise)


def fulfill(promise):
    """
    Block until the `promise` is fulfilled and return the output.
    Raises a `BrokenPromise` exception if the promise is not fulfilled.
    """
    is_fulfilled, result = promise.check_fulfilled()

    if is_fulfilled:
        return result
    else:
        raise BrokenPromise(promise)

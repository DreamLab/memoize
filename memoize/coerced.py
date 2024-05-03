"""
[Internal use only] Some functions work differently way depending if asyncio or Tornado is used - this is resolved here.
"""

import datetime
import importlib.util
import logging
import sys

from memoize.memoize_configuration import force_asyncio

logger = logging.getLogger('memoize')
try:
    if force_asyncio and importlib.util.find_spec('tornado'):
        logger.warning('Forcefully switching to asyncio even though tornado exists')
        raise ImportError()

    from tornado.ioloop import IOLoop
    from tornado import gen
    # ignore for mypy as we don't know any stub source for tornado.platform.asyncio
    from tornado.platform.asyncio import to_asyncio_future # type: ignore
    from tornado.concurrent import Future

    logger.info('Passed tornado availability check - using tornado')

    # ignore for mypy as types are resolved in runtime
    def _apply_timeout(method_timeout: datetime.timedelta, future: Future) -> Future:  # type: ignore
        return gen.with_timeout(method_timeout, future)


    def _call_later(delay: datetime.timedelta, callback):
        IOLoop.current().call_later(delay=delay.total_seconds(), callback=callback)


    def _call_soon(callback, *args):
        return IOLoop.current().spawn_callback(callback, *args)


    def _future():
        return Future()


    def _timeout_error_type():
        return gen.TimeoutError

except ImportError:
    import asyncio

    logger.info('Using asyncio instead of torando')

    # this backported version of `wait_for` is taken from Python 3.11
    # and allows to continue having these `coerced` functions working (they are at least partially based on hacks)
    # in general we need to drop tornado support either way (so this temporary solution would be gone either way)
    async def wait_for(fut, timeout):
        """Wait for the single Future or coroutine to complete, with timeout.

        Coroutine will be wrapped in Task.

        Returns result of the Future or coroutine.  When a timeout occurs,
        it cancels the task and raises TimeoutError.  To avoid the task
        cancellation, wrap it in shield().

        If the wait is cancelled, the task is also cancelled.

        This function is a coroutine.
        """

        from asyncio import events, ensure_future, exceptions
        from asyncio.tasks import _cancel_and_wait, _release_waiter
        import functools
        loop = events.get_running_loop()

        if timeout is None:
            return await fut

        if timeout <= 0:
            fut = ensure_future(fut, loop=loop)

            if fut.done():
                return fut.result()

            await _cancel_and_wait(fut)
            try:
                return fut.result()
            except exceptions.CancelledError as exc:
                raise exceptions.TimeoutError() from exc

        waiter = loop.create_future()
        timeout_handle = loop.call_later(timeout, _release_waiter, waiter)
        cb = functools.partial(_release_waiter, waiter)

        fut = ensure_future(fut, loop=loop)
        fut.add_done_callback(cb)

        try:
            # wait until the future completes or the timeout
            try:
                await waiter
            except exceptions.CancelledError:
                if fut.done():
                    return fut.result()
                else:
                    fut.remove_done_callback(cb)
                    # We must ensure that the task is not running
                    # after wait_for() returns.
                    # See https://bugs.python.org/issue32751
                    await _cancel_and_wait(fut)
                    raise

            if fut.done():
                return fut.result()
            else:
                fut.remove_done_callback(cb)
                # We must ensure that the task is not running
                # after wait_for() returns.
                # See https://bugs.python.org/issue32751
                await _cancel_and_wait(fut)
                # In case task cancellation failed with some
                # exception, we should re-raise it
                # See https://bugs.python.org/issue40607
                try:
                    return fut.result()
                except exceptions.CancelledError as exc:
                    raise exceptions.TimeoutError() from exc
        finally:
            timeout_handle.cancel()

    # ignore for mypy as types are resolved in runtime
    def _apply_timeout(method_timeout: datetime.timedelta, future: asyncio.Future) -> asyncio.Future:  # type: ignore
        if sys.version_info >= (3, 12, 0):
            return wait_for(future, method_timeout.total_seconds())
        else:
            return asyncio.wait_for(future, method_timeout.total_seconds())


    def _call_later(delay: datetime.timedelta, callback):
        asyncio.get_event_loop().call_later(delay=delay.total_seconds(), callback=callback)


    def _call_soon(callback, *args):
        asyncio.get_event_loop().call_soon(asyncio.ensure_future, callback(*args))


    def _future():
        return asyncio.Future()


    def _timeout_error_type():
        try:
            return asyncio.futures.TimeoutError
        except AttributeError:
            return asyncio.TimeoutError

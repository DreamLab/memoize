"""
[Internal use only] Some functions work differently way depending if asyncio or Tornado is used - this is resolved here.
"""

import datetime
import logging

from memoize.memoize_configuration import force_asyncio

logger = logging.getLogger('memoize')
try:
    if force_asyncio:
        logger.warning('Forcefully omitting tornado availability check & switching to asyncio')
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

    # ignore for mypy as types are resolved in runtime
    def _apply_timeout(method_timeout: datetime.timedelta, future: asyncio.Future) -> asyncio.Future:  # type: ignore
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

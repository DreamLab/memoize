"""
[Internal use only] Some functions work differently way depending if asyncio or Tornado is used - this is resolved here.
"""

import datetime
import logging
from typing import Coroutine

from memoize.memoize_configuration import force_asyncio

logger = logging.getLogger('memoize')
try:
    if force_asyncio:
        logger.warning('Forcefully omitting tornado availability check & switching to asyncio')
        raise ImportError()

    from tornado.ioloop import IOLoop
    from tornado import gen
    from tornado.platform.asyncio import to_asyncio_future
    from tornado.concurrent import Future

    logger.info('Passed tornado availability check - using tornado')


    def _apply_timeout(method_timeout: datetime.timedelta, future: Future) -> Future:
        return gen.with_timeout(method_timeout, future)


    def _call_later(delay: datetime.timedelta, callback):
        IOLoop.current().call_later(delay=delay.total_seconds(), callback=callback)


    def _call_soon(callback, *args):
        return IOLoop.current().spawn_callback(callback, *args)


    def _future():
        return Future()

except ImportError:
    import asyncio

    logger.info('Using asyncio instead of torando')


    def _apply_timeout(method_timeout: datetime.timedelta, future: asyncio.Future) -> Coroutine:
        return asyncio.wait_for(future, method_timeout.total_seconds())


    def _call_later(delay: datetime.timedelta, callback):
        asyncio.get_event_loop().call_later(delay=delay.total_seconds(), callback=callback)


    def _call_soon(callback, *args):
        asyncio.get_event_loop().call_soon(asyncio.ensure_future, callback(*args))


    def _future():
        return asyncio.Future()

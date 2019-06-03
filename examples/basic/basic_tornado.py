import random

from tornado import gen
from tornado.ioloop import IOLoop

from memoize.wrapper import memoize


@memoize()
@gen.coroutine
def expensive_computation():
    return 'expensive-computation-' + str(random.randint(1, 100))


@gen.coroutine
def main():
    result1 = yield expensive_computation()
    print(result1)
    result2 = yield expensive_computation()
    print(result2)
    result3 = yield expensive_computation()
    print(result3)


if __name__ == "__main__":
    IOLoop.current().run_sync(main)

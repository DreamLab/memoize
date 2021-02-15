from datetime import timedelta

from tornado import gen
from tornado.ioloop import IOLoop

from memoize.configuration import DefaultInMemoryCacheConfiguration
from memoize.wrapper import memoize

# scenario configuration
concurrent_requests = 5
request_batches_execution_count = 50
cached_value_ttl_ms = 200
delay_between_request_batches_ms = 70

# results/statistics
unique_calls_under_memoize = 0


@memoize(configuration=(DefaultInMemoryCacheConfiguration(update_after=timedelta(milliseconds=cached_value_ttl_ms))))
@gen.coroutine
def cached_with_memoize():
    global unique_calls_under_memoize
    unique_calls_under_memoize += 1
    yield gen.sleep(0.01)
    return unique_calls_under_memoize


@gen.coroutine
def main():
    for i in range(request_batches_execution_count):
        res = yield [x() for x in [cached_with_memoize] * concurrent_requests]
        print(res)
        # yield [x() for x in [cached_with_different_cache] * concurrent_requests]
        yield gen.sleep(delay_between_request_batches_ms / 1000)

    print("Memoize generated {} unique backend calls".format(unique_calls_under_memoize))
    predicted = (delay_between_request_batches_ms * request_batches_execution_count) // cached_value_ttl_ms
    print("Predicted (according to TTL) {} unique backend calls".format(predicted))

    # Printed:
    # Memoize generated 17 unique backend calls
    # Predicted (according to TTL) 17 unique backend calls

if __name__ == "__main__":
    IOLoop.current().run_sync(main)

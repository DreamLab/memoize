import asyncio


def _as_future(value):
    future = asyncio.Future()
    if isinstance(value, Exception):
        future.set_exception(value)
    else:
        future.set_result(value)
    return future


async def _ensure_background_tasks_finished():
    # let other tasks to acquire IO loop
    for i in range(10):
        await asyncio.sleep(0)


async def _ensure_asyncio_background_tasks_finished():
    # let other tasks to acquire IO loop
    for i in range(10):
        await asyncio.sleep(0)


class AnyObject(object):
    def __eq__(self, o: object) -> bool:
        return True


def _assert_called_once_with(mock, args, kwargs):
    """Mock assertions do not support "any" placeholders. This method allows to use AnyObject as any argument."""
    calls_list = mock.call_args_list
    assert 1 == len(calls_list), 'Called {} times but expected only one call'.format(len(calls_list))
    call_args, call_kwargs = calls_list[0]

    for arg_num in range(len(args)):
        expected = args[arg_num]
        got = call_args[arg_num]
        assert expected.__eq__(got), 'Arguments at position {} mismatch: {} != {}'.format(arg_num, expected, got)

    for kwarg_key in set(kwargs.keys()).union(set(call_kwargs.keys())):
        expected = args[kwarg_key]
        got = call_args[kwarg_key]
        assert expected.__eq__(got), 'Arguments under key {} mismatch: {} != {}'.format(kwarg_key, expected, got)

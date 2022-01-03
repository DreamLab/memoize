def fix_python_3_10_compatibility():
    import collections
    collections.MutableMapping = collections.abc.MutableMapping  # workaround for python 3.10

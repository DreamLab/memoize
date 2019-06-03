"""
[API] Provides global config of the library.
Translates environment variables into values used internally by the library.
"""

import os

force_asyncio = bool(os.environ.get('MEMOIZE_FORCE_ASYNCIO', False))

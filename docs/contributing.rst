Contributing
============

Coverage
--------

All test cases/scenarios & coverage are executed by tox:

.. code-block:: bash

   tox

For users who use multiple interpreters:

.. code-block:: bash

   # python3.8 is just an example
   python3.8 -m tox

To run testing scenarios in IDE of your choice please see ``tox.ini``
(especially take a look how ``MEMOIZE_FORCE_ASYNCIO`` is used).

Docs
----

Before submitting pull request please update modules apidocs & ensure documentation generates properly.
The following commands will do both (watch for errors & warnings).

.. code-block:: bash

   pip install sphinx sphinx_rtd_theme
   cd docs
   rm -rf source/*
   sphinx-apidoc --doc-project "API docs" -o source/ ../memoize
   make html

PyPi
----

.. code-block:: bash

    # build dist
    python3 -m pip install --user --upgrade setuptools wheel
    python3 setup.py sdist bdist_wheel

    # try package
    python3 -m pip install --user --upgrade twine
    python3 -m twine check dist/*

    # actual upload will be done by GitHub Actions

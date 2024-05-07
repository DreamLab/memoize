2.1.0
-----

* Added configurable postprocessing, that allows to modify value retrieved from the cache
  * Added built-in implementation, that applies deep-copy
* Fixed missing invalidation module in api docs
* Fixed MANIFEST.in

2.0.0
-----

* Changed exception handling
  * now exceptions are chained (before they were added in `args`)
  * timeout errors are now chained (before they were not included at all)
  * in case of dogpiling, all callers are now notified about the error (see issue #23)

1.2.2
-----

* Fixed an example, that used deprecated `utcnow`

1.2.1
-----

* Fixed UTC related deprecation warnings in Python 3.12+

1.2.0
-----

* Added support for Python 3.12
* Added warning that support for Tornado is deprecated and will be removed in future
  (it causes more and more hacks/workarounds while Tornado importance is diminishing).

1.1.5
-----

* Expanded docs adding section on how to achieve granular expire/update time control (different settings per entry).
* Minor fix for contribution guide (after migration, Travis was still mentioned instead of GitHub Actions).

1.1.4
-----

* Fixed redundant waring if `tornado` is not available to be used (silenced).
* Fixed GitHub Actions build (python 3.5 & 3.6 no longer available).

1.1.3
-----

* Fixed declared supported python versions (`classifiers` in `setup.py`).

1.1.2
-----

* Added support for Python 3.10:
   * Applied workaround for testing setup (`MutableMapping` alias required by `tornado.testing.gen_test`);
   * Updated `mypy` and `coverage` setup to Python 3.10.
* Added support for Python 3.11 (provisional as only alpha releases of 3.11 were tested).

1.1.1
-----

* Fixed parallel queries returning expired entries (while expired entry was being refreshed).

1.1.0
-----

* Added support for manual invalidation.
* Added customization of basic params for DefaultInMemoryCacheConfiguration.
* Included initial mypy checking (tornado/asyncio interoperability forces some ignores).

1.0.4
-----

* Added support for Python 3.9.

1.0.3
-----

* Fixed unhandled KeyError in UpdateStatuses.

1.0.2
-----

* Added support for Python 3.8.

1.0.1
-----

* Removed unintended dependency on tornado (it prevented asyncio mode working without tornado installed).

1.0.0
-----

* Initial public release.

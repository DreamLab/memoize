try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def prepare_description():
    description = open('README.rst', 'rb').read().decode('utf-8')
    # class references work well in generated docs (render links to API docs)
    # but don't work at PyPi - therefore are removed
    description = description.replace(":class:", "")
    return description


setup(
    name='py-memoize',
    version='1.1.3',
    author='Michal Zmuda',
    author_email='zmu.michal@gmail.com',
    url='https://github.com/DreamLab/memoize',
    maintainer='DreamLab',
    packages=['memoize'],
    test_suite='tests',
    license='Apache License 2.0',
    description=('Caching library for asynchronous Python applications (both based on asyncio and Tornado) '
                 'that handles dogpiling properly and provides a configurable & extensible API.'),
    long_description=prepare_description(),
    long_description_content_type="text/x-rst",
    platforms=['Any'],
    keywords='python cache tornado asyncio',
    install_requires=None,
    extras_require={
        'tornado': ['tornado>4,<5'],
        'ujson': ['ujson>=1.35,<2'],
    },
    classifiers=[
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers'
    ]
)

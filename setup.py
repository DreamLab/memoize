try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='memoize',
    version='1.0.0',
    author='Michal Zmuda',
    author_email='zmu.michal@gmail.com',
    maintainer='DreamLab',
    packages=['memoize'],
    test_suite='tests',
    license='Apache License 2.0',
    description=('Caching library for asynchronous Python applications (both based on asyncio and Tornado) '
                 'that handles dogpiling properly and provides a configurable & extensible API.'),
    long_description=open('README.rst', 'rb').read().decode('utf-8'),
    platforms=['Any'],
    keywords='python cache tornado asyncio',
    install_requires=None,
    extras_require={
        'tornado': ['tornado>4,<5'],
        'ujson': ['ujson>=1.35'],
    },
    classifiers=[
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5'
        'Programming Language :: Python :: 3.6'
        'Programming Language :: Python :: 3.7'
        'Intended Audience :: Developers'
    ]
)

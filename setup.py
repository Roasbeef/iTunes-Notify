"""
iTunes-Notify
========

.. image:: https://github.com/Roasbeef/iTunes-Notify
   :align: left

Installation
============

Installing using pip. ::

    pip install itunesnotify

Using iTunes-Notify
==============

Available commands. ::

    itunes-notify run
    # start the notification process

    itunes-notify stop
    # end the notification process

"""

import os
import sys

try:
        from setuptools import setup
except ImportError:
        from distutils.core import setup


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from itunesnotify.core import __version__


def publish():
    os.system("python setup.py sdist upload")

if sys.argv[-1] == "publish":
    publish()
    sys.exit()

dependencies = ['gntp', 'docopt']

setup(
    name='itunesnotify',
    version=".".join(str(x) for x in __version__),
    description='Providing song notifications for iTunes on Mac OSX',
    url='https://github.com/Roasbeef/iTunes-Notify',
    author='Olaoluwa Osuntokun',
    author_email='laolu32@gmail.com',
    install_requires=dependencies,
    tests_require=['tox==1.3'],
    packages=['itunesnotify', ],
    license='The Unlicense',
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            'itunes-notify = itunesnotify.cli:begin',
        ],
    },
)

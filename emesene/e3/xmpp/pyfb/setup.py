#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

__version__ = "0.3.2"

setup(
    name='pyfb',
    version=__version__,
    description='A Python Interface to the Facebook Graph API',
    author='Juan Manuel García',
    author_email = "jmg.utn@gmail.com",
    license = "GPL v3",
    keywords = "Facebook Graph API Wrapper Python",
    url='http://code.google.com/p/pyfb/',
    packages=['pyfb'],
    install_requires=[
        'simplejson',
    ],
)

#!/usr/bin/env python
# coding: utf8
"""
Flask-Optimize
-------------

Adds support for optimizing PNG, GIF, and JPEG images.
"""

from setuptools import setup

setup(
    name='Flask-Optimize',
    version='0.1',
    url='https://github.com/impressiver/flask-optimize',
    license='MIT',
    author='Ian White',
    author_email='ian@impressiver.com',
    description='Image optimization for Flask',
    long_description=__doc__,
    py_modules=['flask_optimize'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask>=0.8'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
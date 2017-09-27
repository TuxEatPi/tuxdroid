#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pip.req import parse_requirements
from pip.download import PipSession
from setuptools import setup


long_desc = """Poor Tux needs a new heart. We do that by feeding it a raspberrypi.

The end goal is to keep Tux's basic functionnality:

- Wings position detection, push buttons and movement
- Mouth movement and position detection
- Eyes position detection, photodetector and lights
- Head button
- Speaker and microphone
- Volume button
"""

session = PipSession()

packages = [
            'tuxdroid',
            ]

install_reqs = parse_requirements('requirements.txt', session=session)
test_reqs = parse_requirements('test_requirements.txt', session=session)

setup(
    name='tuxdroid',
    version='0.0.1',
    packages=packages,
    description="""New TuxDroid heart powered by Raspberry pi""",
    long_description=long_desc,
    author="TuxEatPi Team",
    # TODO create team mail
    author_email='titilambert@gmail.com',
    url="https://github.com/TuxEatPi/tuxdroid",
    download_url="https://github.com/TuxEatPi/tuxdroid/archive/0.0.1.tar.gz",
    package_data={'': ['LICENSE.txt']},
    package_dir={'tuxdroid': 'tuxdroid'},
    include_package_data=True,
    license='Apache 2.0',
    classifiers=(
        'Programming Language :: Python :: 3.5',
    ),
    install_requires=[str(r.req) for r in install_reqs],
    tests_require=[str(r.req) for r in test_reqs],
)

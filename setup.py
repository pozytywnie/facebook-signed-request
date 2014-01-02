#!/usr/bin/env python
from distutils.core import setup

setup(
    name='facebook-signed-request',
    version='1.2.10',
    maintainer="Tomasz Wysocki",
    maintainer_email="tomasz@wysocki.info",
    install_requires=(
        'django',
    ),
    packages=[
        'facebook_signed_request',
    ],
)

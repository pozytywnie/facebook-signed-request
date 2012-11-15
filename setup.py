#!/usr/bin/env python
from distutils.core import setup

setup(
    name='facebook-signed-request',
    version='1.2.3',
    maintainer="Tomasz Wysocki",
    maintainer_email="tomasz@wysocki.info",
    install_requires=(
        'django',
        'django-package-installer',
    ),
    packages=[
        'facebook_signed_request',
    ],
)

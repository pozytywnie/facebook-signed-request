from django.conf.urls import include
from django.conf.urls import patterns
from package_installer import Package


class FacebookSignedRequestPackage(Package):
    INSTALL_APPS = ('facebook_signed_request',)

PACKAGE = FacebookSignedRequestPackage()

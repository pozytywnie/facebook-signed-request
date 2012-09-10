from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from package_installer import Package

class FacebookSignedRequestPackage(Package):
    INSTALL_APPS = ('facebook_signed_request',)

PACKAGE = FacebookSignedRequestPackage()

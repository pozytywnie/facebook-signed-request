from django.conf import settings
from django.core import exceptions

def validate():
    """ Check occurrence of following constants in settings:

    FACEBOOK_APP_SECRET - application id in Facebook system. Can be found on app
                      configuration screen as "App Secret".

    """
    SECRET_VAR = 'FACEBOOK_APP_SECRET'
    if not hasattr(settings, SECRET_VAR):
        raise exceptions.ImproperlyConfigured(
            "To work with Facebook provide %s in settings.py." % SECRET_VAR
        )
    id = getattr(settings, SECRET_VAR)
    if not isinstance(id, basestring):
        raise exceptions.ImproperlyConfigured(
            "%s must be string, but is %s" % (SECRET_VAR, id.__class__.__name__)
        )

validate()

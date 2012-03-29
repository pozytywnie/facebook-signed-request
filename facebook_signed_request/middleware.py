import base64
import hashlib
import hmac
import time
import logging

from django.conf import settings
from django.contrib.auth import logout, authenticate, login
from django.http import QueryDict
from django.utils import simplejson as json

logger = logging.getLogger(__name__)

EXPIRATION_TIME = 5 * 60

class SignedRequestException(Exception):
    pass

class SignedRequestMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST' and 'signed_request' in request.POST:
            try:
                raw_signature, payload = request.POST['signed_request'].split('.', 1)
                signature = self.decode_data(raw_signature)
                data = json.loads(self.decode_data(payload))
                self.verify_signature(data, payload, signature)
                self.validate_time(data['issued_at'])
                request.facebook = data
            except ValueError: # json loads & split
                logger.error('"signed_request" is invalid json string')
            except TypeError: # base64 decode
                logger.error('Cannot decode "signed_request"')
            except SignedRequestException as exception:
                logger.error(exception.message)
            request.POST = QueryDict('')
            request.method = 'GET'

    def decode_data(self, data):
        padding = "=" * ((4 - len(data) % 4) % 4)
        return base64.urlsafe_b64decode(str(data) + padding)

    def validate_time(self, timestamp):
        now = time.time()
        if timestamp + EXPIRATION_TIME < now:
            raise SignedRequestException('"signed_request" expired')

    def verify_signature(self, data, payload, signature):
        def get_algorithm(name):
            name = name.lower()
            if name[:5] != "hmac-" or name[5:] not in hashlib.algorithms:
                raise SignedRequestException('Unsupported hash algorithm')
            return getattr(hashlib, name[5:])

        expected = hmac.new(settings.FACEBOOK_APP_SECRET, payload, get_algorithm(data['algorithm'])).digest()
        if expected != signature:
            raise SignedRequestException('Wrong signature')

class FacebookLoginMiddleware(object):
    def process_request(self, request):
        # this import is not at beggining, because we don't want to make dependencies on whole app, but only on this class
        # if programmer uses facebook_signed_request.FacebookLoginMiddleware without facebook_auth
        # he will get import exception
        from facebook_auth.models import FacebookUser
        if hasattr(request, 'facebook'):
            fb_data = request.facebook
            if not 'user' in fb_data and isinstance(request.user, FacebookUser):
                logout(request)
            if 'user' in fb_data:
                self.login_user(request, fb_data)

    def login_user(self, request, fb_data):
        if 'oauth_token' in fb_data:
            if not self.users_match(fb_data, request.user):
                if request.user.is_authenticated():
                    logout(request)
                self.login_by_facebook_data(request, fb_data)

    def users_match(self, fb_user, user):
        return user.is_authenticated() and hasattr(user, 'access_token') and fb_user['oauth_token'] == user.access_token

    def login_by_facebook_data(self, request, fb_user):
        user = authenticate(access_token=fb_user['oauth_token'])
        if user:
            login(request, user)


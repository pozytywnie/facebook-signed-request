import base64
import hashlib
import hmac
import logging
import time

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.db.models import get_model
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
            debug = {'expected': expected, 'gotten': signature, 'payload': payload, 'data': data}
            raise SignedRequestException('Wrong signature', debug)

class FacebookLoginMiddleware(object):
    def process_request(self, request):
        if hasattr(request, 'facebook'):
            fb_data = request.facebook
            if not isinstance(request.user, get_model('facebook_auth', 'FacebookUser')):
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

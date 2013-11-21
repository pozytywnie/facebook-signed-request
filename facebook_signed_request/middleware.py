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


class SignedRequestException(Exception):
    pass

class SignedRequestMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST' and 'signed_request' in request.POST:
            try:
                data = SignedRequestParser(request.POST['signed_request']).parse()
                request.facebook = data
            except SignedRequestException as exception:
                logger.exception(exception)
            request.POST = QueryDict('')
            request.method = 'GET'


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


class SignedRequestParser(object):
    def __init__(self, signed_request):
        self.signed_request = signed_request

    def parse(self):
        raw_signature, payload = self._split_signed_request()
        signature = self._decode_signature(raw_signature)
        data = self._decode_payload(payload)
        self.verify_signature(data, payload, signature)
        return data

    def _split_signed_request(self):
        try:
            return self.signed_request.split('.', 1)
        except ValueError:
            raise SignedRequestException('Cannot split signature and payload')

    def _decode_signature(self, raw_signature):
        try:
            return self._decode_data(raw_signature)
        except TypeError:
            raise SignedRequestException('Cannot base64 decode signature')

    def _decode_payload(self, payload):
        try:
            decoded = self._decode_data(payload)
        except TypeError:
            raise SignedRequestException('Cannot base64 decode data')
        else:
            try:
                return json.loads(decoded)
            except ValueError:
                raise SignedRequestException('Invalid json')

    def _decode_data(self, data):
        padding = "=" * ((4 - len(data) % 4) % 4)
        return base64.urlsafe_b64decode(str(data) + padding)

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

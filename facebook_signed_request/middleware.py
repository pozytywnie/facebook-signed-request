import base64
import time

from django.http import QueryDict
from django.utils import simplejson as json
import logging

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
                self.validate_time(data['issued_at'])
                request.facebook = data
            except ValueError: # json loads & split
                logger.error('"signed_request" is invalid json string')
                pass
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

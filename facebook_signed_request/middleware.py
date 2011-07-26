import base64

from django.http import QueryDict
from django.utils import simplejson as json
import logging

logger = logging.getLogger(__name__)

class SignedRequestMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST' and 'signed_request' in request.POST:
            try:
                raw_signature, payload = request.POST['signed_request'].split('.', 1)
                signature = self.decode_data(raw_signature)
                data = json.loads(self.decode_data(payload))
                request.facebook = data
            except ValueError: # json loads & split
                logger.error('"signed_request" is invalid json string')
                pass
            except TypeError: # base64 decode
                logger.error('Cannot decode "signed_request"')
            request.POST = QueryDict('')
            request.method = 'GET'

    def decode_data(self, data):
        padding = "=" * ((4 - len(data) % 4) % 4)
        return base64.urlsafe_b64decode(str(data) + padding)


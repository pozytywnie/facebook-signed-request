# facebook-signed-request
Django application for handling Facebook signed request. Validates and extracts data that could be handy for any Facebook application.


Usage
-----

Add to MIDDLEWARE_CLASSES:

    # somewhere at top, after CommonMiddleware
    'facebook_javascript_authentication.middlewares.P3PMiddleware',
    'facebook_signed_request.middleware.SignedRequestMiddleware',
    # somewhere lower on the list
    'facebook_signed_request.middleware.FacebookLoginMiddleware',


In a view data from a signed request will be under request.facebook

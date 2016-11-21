from rest_framework.authentication import (BaseAuthentication,
                                           SessionAuthentication)
from rest_framework import exceptions
from django.contrib.auth import authenticate


class TokenAPIAuthentication(BaseAuthentication):
    """Django-tokenapi authentication.
    https://github.com/jpulgarin/django-tokenapi/

    If user/token pair wasn't able to authenticate authenticate_credentials will
    try BasicAuthentication method to login. In this case we assume user
    variable will contain a valid username and token variable will contain its
    related password.
    """
    def authenticate(self, request):
        user = None
        token = None
        basic_auth = request.META.get("HTTP_AUTHORIZATION")

        if basic_auth:
            auth_method, auth_string = basic_auth.split(' ', 1)

            if auth_method.lower() == 'basic':
                auth_string = auth_string.strip().decode('base64')
                user, token = auth_string.split(':', 1)

        if not (user and token):
            user = request.REQUEST.get('user')
            token = request.REQUEST.get('token')

            if not user or not token:
                raise exceptions.AuthenticationFailed("Must include 'user'/'username' and 'token'/'password' parameters with request.")

        if user and token:
            return self.authenticate_credentials(user, token)
        else:
            return None

    def authenticate_credentials(self, user, token):
        try:
            user = authenticate(pk=user, token=token)
        except:
            raise exceptions.AuthenticationFailed("Must include 'user'/'username' and 'token'/'password' parameters with request.")
        
        if user is None:
            raise exceptions.AuthenticationFailed("Invalid user/token pair.")

        return (user, None)


class SuperUserSessionAuthentication(SessionAuthentication):
    """
    Use Django's session framework for authentication of super users.
    # http://www.kerseydev.com/2014/01/custom-authentication-scheme-django-rest-framework/
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        # Get the underlying HttpRequest object
        request = request._request
        user = getattr(request, 'user', None)

        # Unauthenticated, CSRF validation not required
        if not user or not user.is_active or not user.is_superuser:
            return None

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)

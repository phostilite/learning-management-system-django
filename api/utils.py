from rest_framework.authentication import TokenAuthentication, get_authorization_header
from rest_framework import exceptions

class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth:
            return None

        if auth[0].lower() != self.keyword.lower().encode():
            # Try default token authentication if it's not a Bearer token
            if auth[0].lower() == b'token':
                auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
                if len(auth_header) == 2 and auth_header[0].lower() == 'token':
                    try:
                        token = auth_header[1]
                        return self.authenticate_credentials(token)
                    except Exception:
                        return None
            return None

        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)
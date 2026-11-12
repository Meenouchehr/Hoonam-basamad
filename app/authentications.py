
import  jwt
from rest_framework import status
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication,SessionAuthentication
from django.utils.translation import gettext as _

from app.exceptions import ProjectException
from django.conf import settings
from datetime import datetime
from app.models import TokenModel
from app.player import get_player_id


class BearerTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'
    model = TokenModel


    def authenticate(self, request):    
        _ret = super().authenticate(request._request)
        if _ret:
            _user,_token = _ret
            _object      = jwt.decode(_token.key, key=settings.SECRET_KEY, algorithms=settings.SECRET_ALGORITM)
            _player_id   = _object['player_id']
            _expires_at  = _object['expires_at']
            date_time_exp = datetime.strptime(_expires_at, '%B %d %Y - %H:%M:%S')
            date_time_now = datetime.strptime(datetime.utcnow().strftime('%B %d %Y - %H:%M:%S'), '%B %d %Y - %H:%M:%S')
            _req_player_id = get_player_id(request)[0]
            if _player_id != _req_player_id:
                raise ProjectException(441,_("Unauthorized"),_("The token is invalid for this system."),status.HTTP_401_UNAUTHORIZED)
                # raise exceptions.AuthenticationFailed(detail={'error': {'code':441,'message':'Unauthorized','detail':'The token is invalid for this system.'}})
            elif date_time_exp < date_time_now:
                raise ProjectException(442,_("Unauthorized"),_("The access token has expired."),status.HTTP_401_UNAUTHORIZED)
                # raise exceptions.AuthenticationFailed(detail={'error': {'code':442,'message':'Unauthorized','detail':'The access token has expired.'}})
        return _ret


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening
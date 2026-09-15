"""
WeChat mini-program authentication endpoints.

Two-step model (see docs/ARCHITECTURAL_DECISION_RECORDS.md):
- Bind: first launch authenticates an existing staff User with username/password
  plus a wx.login code, then links the WeChat openid to that User and issues JWTs.
- Login: later launches exchange a wx.login code for JWTs via the stored openid.
  An unbound openid returns {'bound': False} so the client shows the bind screen.

Both endpoints are unauthenticated (AllowAny); every other API requires JWT.
"""
from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import WeChatIdentity
from accounts.wechat import WeChatAuthError, code2session

from .serializers import UserSerializer


def _tokens_for(user):
    """Mint a SimpleJWT access/refresh pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class WeChatBindView(APIView):
    """Bind a WeChat openid to an existing staff account, then issue tokens."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        code = request.data.get('code')
        username = request.data.get('username')
        password = request.data.get('password')
        if not (code and username and password):
            return Response(
                {'error': 'code, username and password are required.'}, status=400
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials.'}, status=401)
        if not user.is_active:
            return Response({'error': 'Account is disabled.'}, status=403)

        try:
            session = code2session(code)
        except WeChatAuthError as exc:
            return Response({'error': str(exc)}, status=400)

        appid = settings.WECHAT_MINI_APPID
        openid = session['openid']
        existing = WeChatIdentity.objects.filter(appid=appid, openid=openid).first()
        if existing is not None and existing.user_id != user.id:
            return Response(
                {'error': 'This WeChat account is already bound to another user.'},
                status=409,
            )

        WeChatIdentity.objects.update_or_create(
            appid=appid,
            openid=openid,
            defaults={'user': user, 'unionid': session.get('unionid', '')},
        )
        return Response(
            {'bound': True, 'user': UserSerializer(user).data, **_tokens_for(user)},
            status=200,
        )


class WeChatLoginView(APIView):
    """Seamless login: exchange a wx.login code for tokens via the stored openid."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'code is required.'}, status=400)

        try:
            session = code2session(code)
        except WeChatAuthError as exc:
            return Response({'error': str(exc)}, status=400)

        appid = settings.WECHAT_MINI_APPID
        identity = (
            WeChatIdentity.objects.filter(appid=appid, openid=session['openid'])
            .select_related('user')
            .first()
        )
        if identity is None or identity.user is None or not identity.user.is_active:
            return Response({'bound': False}, status=200)

        unionid = session.get('unionid', '')
        if unionid and identity.unionid != unionid:
            identity.unionid = unionid
            identity.save(update_fields=['unionid', 'updated_at'])

        return Response(
            {
                'bound': True,
                'user': UserSerializer(identity.user).data,
                **_tokens_for(identity.user),
            },
            status=200,
        )

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
from django.db.models import Q
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User, WeChatIdentity
from accounts.wechat import WeChatAuthError, code2session

from .serializers import UserSerializer


def _tokens_for(user):
    """Mint a SimpleJWT access/refresh pair for a user."""
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def resolve_field_engineers(*, chinese_name='', phone='', wechat_id='', invite_code='', query=''):
    """Return active Users matching any provided field-engineer identifier.

    Supports lookup by Chinese name, phone number, WeChat id, or invite code.
    ``query`` is a convenience that tries all four at once.
    """
    filters = Q()
    if chinese_name:
        filters |= Q(chinese_name__iexact=chinese_name)
    if phone:
        filters |= Q(phone_number=phone)
    if wechat_id:
        filters |= Q(wechat_id__iexact=wechat_id)
    if invite_code:
        filters |= Q(invite_code__iexact=invite_code)
    if query:
        filters |= (
            Q(chinese_name__iexact=query)
            | Q(phone_number=query)
            | Q(wechat_id__iexact=query)
            | Q(invite_code__iexact=query)
        )
    if not filters:
        return User.objects.none()
    return User.objects.filter(is_active=True).filter(filters)


class WeChatLookupView(APIView):
    """Resolve a field engineer to matching account(s) for login confirmation.

    Unauthenticated. The mini program bind screen calls this after the engineer
    supplies a Chinese name, phone number, WeChat id, or invite code, then shows
    the English name to confirm before the password step. Returns all active
    matches so the client can disambiguate.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        chinese_name = (request.data.get('chinese_name') or '').strip()
        phone = (request.data.get('phone') or request.data.get('phone_number') or '').strip()
        wechat_id = (request.data.get('wechat_id') or '').strip()
        invite_code = (request.data.get('invite_code') or '').strip()
        query = (request.data.get('query') or '').strip()
        if not (chinese_name or phone or wechat_id or invite_code or query):
            return Response({'error': 'A lookup identifier is required.'}, status=400)

        users = resolve_field_engineers(
            chinese_name=chinese_name, phone=phone, wechat_id=wechat_id,
            invite_code=invite_code, query=query,
        )
        matches = [
            {
                'username': u.username,
                'english_name': u.get_full_name() or u.username,
                'chinese_name': u.chinese_name,
                'phone_number': u.phone_number,
                'has_invite_code': bool(u.invite_code),
            }
            for u in users
        ]
        return Response({'found': bool(matches), 'matches': matches}, status=200)


class WeChatProfileCompleteView(APIView):
    """One-time self-service profile completion for a freshly bound engineer.

    A field engineer created from an invite code has no contact details yet, so
    the mini program collects Chinese name / phone / WeChat id on first login.
    Only blank fields are written: admin-maintained values are never overwritten
    by the client, which makes the call safely repeatable.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        chinese_name = (request.data.get('chinese_name') or '').strip()
        phone = (request.data.get('phone_number') or request.data.get('phone') or '').strip()
        wechat_id = (request.data.get('wechat_id') or '').strip()
        if not (chinese_name or phone or wechat_id):
            return Response({'error': 'Nothing to update.'}, status=400)

        updated = []
        if chinese_name and not user.chinese_name:
            user.chinese_name = chinese_name
            updated.append('chinese_name')
        if phone and not user.phone_number:
            user.phone_number = phone
            updated.append('phone_number')
        if wechat_id and not user.wechat_id:
            user.wechat_id = wechat_id
            updated.append('wechat_id')
        if updated:
            user.save(update_fields=updated + ['updated_at'])
        return Response(
            {'updated': updated, 'user': UserSerializer(user).data},
            status=200,
        )


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

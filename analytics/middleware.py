import hashlib
import re
from django.utils import timezone
from .models import PageVisit


# Paths to ignore — admin, static, favicon, API health checks
IGNORE_PATTERNS = [
    re.compile(r'^/django-admin/'),
    re.compile(r'^/static/'),
    re.compile(r'^/media/'),
    re.compile(r'^/favicon\.ico$'),
    re.compile(r'^/robots\.txt$'),
    re.compile(r'^/sitemap\.xml$'),
    re.compile(r'^/health/?$'),
]

# Simple bot detection
BOT_KEYWORDS = [
    'bot', 'crawler', 'spider', 'crawling',
    'googlebot', 'bingbot', 'yandex', 'baidu',
    'facebookexternalhit', 'slackbot', 'telegrambot',
    'whatsapp', 'curl', 'wget', 'python-requests',
]


def _hash_ip(ip):
    """SHA-256 hash of IP. Not reversible."""
    if not ip:
        return ''
    return hashlib.sha256(ip.encode('utf-8')).hexdigest()[:32]


def _is_bot(user_agent):
    if not user_agent:
        return True
    ua = user_agent.lower()
    return any(k in ua for k in BOT_KEYWORDS)


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class VisitTrackingMiddleware:
    """
    Records a PageVisit row for every interesting GET request.
    Skips static files, admin, health checks, and bots.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only track GET requests that returned OK
        if request.method != 'GET' or response.status_code >= 400:
            return response

        # Skip ignored paths
        path = request.path
        for pattern in IGNORE_PATTERNS:
            if pattern.match(path):
                return response

        # Skip if not HTML
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response

        try:
            ua = request.META.get('HTTP_USER_AGENT', '')
            is_bot = _is_bot(ua)

            PageVisit.objects.create(
                path=path[:255],
                method=request.method,
                ip_hash=_hash_ip(_get_client_ip(request)),
                user_agent=ua[:500],
                referer=request.META.get('HTTP_REFERER', '')[:500],
                session_key=(request.session.session_key or '')[:64],
                user=request.user if request.user.is_authenticated else None,
                is_bot=is_bot,
            )
        except Exception:
            # Never let analytics break the request
            pass

        return response
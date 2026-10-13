from datetime import timedelta
from django.utils import timezone
from django.db.models import Count
from .models import PageVisit


def dashboard_stats(days=14):
    """
    Returns all the metrics the super admin dashboard needs.
    All queries filter out bots.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    humans = PageVisit.objects.filter(is_bot=False)

    # ---- Headline counts ----
    pageviews_today = humans.filter(created_at__gte=today_start).count()
    pageviews_yesterday = humans.filter(
        created_at__gte=yesterday_start, created_at__lt=today_start
    ).count()

    unique_today = humans.filter(
        created_at__gte=today_start
    ).values('ip_hash').exclude(ip_hash='').distinct().count()

    pageviews_week = humans.filter(created_at__gte=week_start).count()
    unique_week = humans.filter(
        created_at__gte=week_start
    ).values('ip_hash').exclude(ip_hash='').distinct().count()

    pageviews_month = humans.filter(created_at__gte=month_start).count()
    unique_month = humans.filter(
        created_at__gte=month_start
    ).values('ip_hash').exclude(ip_hash='').distinct().count()

    # ---- Chart: pageviews per day for last N days ----
    chart = []
    for i in range(days - 1, -1, -1):
        day = today_start - timedelta(days=i)
        next_day = day + timedelta(days=1)
        pv = humans.filter(created_at__gte=day, created_at__lt=next_day).count()
        uv = humans.filter(
            created_at__gte=day, created_at__lt=next_day
        ).values('ip_hash').exclude(ip_hash='').distinct().count()
        chart.append({
            'label': day.strftime('%d %b'),
            'pageviews': pv,
            'visitors': uv,
        })

    # ---- Top pages ----
    top_pages = list(
        humans.filter(created_at__gte=week_start)
        .values('path')
        .annotate(views=Count('id'))
        .order_by('-views')[:8]
    )

    # ---- Referrers ----
    top_referers = list(
        humans.filter(created_at__gte=week_start)
        .exclude(referer='')
        .values('referer')
        .annotate(views=Count('id'))
        .order_by('-views')[:5]
    )

    # ---- Recent visitors (last 20) ----
    recent = humans.select_related('user').order_by('-created_at')[:20]

    return {
        'pageviews_today': pageviews_today,
        'pageviews_yesterday': pageviews_yesterday,
        'unique_today': unique_today,
        'pageviews_week': pageviews_week,
        'unique_week': unique_week,
        'pageviews_month': pageviews_month,
        'unique_month': unique_month,
        'chart': chart,
        'top_pages': top_pages,
        'top_referers': top_referers,
        'recent': recent,
    }
from django.db import models


class PageVisit(models.Model):
    """
    One record per page load. Lightweight, aggregated in the dashboard.
    No PII stored beyond hashed IP.
    """
    # ---- What was visited ----
    path = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=10, default='GET')

    # ---- Who visited (anonymized) ----
    ip_hash = models.CharField(max_length=64, db_index=True, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.CharField(max_length=500, blank=True)

    # ---- Session tracking ----
    session_key = models.CharField(max_length=64, db_index=True, blank=True)

    # ---- If they're logged in, link them ----
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='page_visits',
    )

    # ---- Meta ----
    is_bot = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Page Visit'
        verbose_name_plural = 'Page Visits'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'is_bot']),
            models.Index(fields=['path', '-created_at']),
        ]

    def __str__(self):
        return f'{self.path} — {self.created_at.strftime("%d %b, %H:%M")}'
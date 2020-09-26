from django.db import models
from datetime import timedelta
from django.utils import timezone


class Block(models.Model):
    AD = 'ad'
    LACK_OF_RECORDS = 'lack of records'
    RATE_LIMIT = 'rate limit'
    RECENT_POSTS = 'recent posts'

    REASONS = (
        (AD, 'ad'),
        (LACK_OF_RECORDS, 'lack of records'),
        (RATE_LIMIT, 'rate limit'),
        (RECENT_POSTS, 'recent posts'),
    )

    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    active_before = models.DateTimeField(null=True, blank=False)
    reason = models.CharField(null=True, choices=REASONS, max_length=64, blank=False)
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, null=True, related_name='blocks', blank=False)

    def activate(self, group, reason, period_in_minutes):
        fields = ['reason', 'active_before', 'is_active', 'group']
        now = timezone.now()

        self.active_before = now + timedelta(minutes=period_in_minutes)
        self.reason = reason
        self.group = group
        self.is_active = True

        self.save(update_fields=fields)

    def deactivate(self):
        fields = ['is_active']

        self.is_active = False

        self.save(update_fields=fields)

    def is_block_active(self):
        if self.is_active and timezone.now() >= self.active_before:
            self.deactivate()
        return self.is_active

    def __str__(self):
        return \
            f'Block {self.id} {self.is_active is True} for group {self.group} before {self.active_before}'

    def __repr__(self):
        return \
            f'Block {self.id} {self.is_active is True} for group {self.group} before {self.active_before}'

    class Meta:
        verbose_name = 'Блокировка'
        verbose_name_plural = 'Блокировки'

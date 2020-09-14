from django.db import models
from datetime import timedelta
from django.utils import timezone


class Block(models.Model):
    AD = 'ad'
    LACK_OF_RECORDS = 'lack of records'
    RATE_LIMIT = 'rate limit'

    REASONS = (
        (AD, 'ad'),
        (LACK_OF_RECORDS, 'lack of records'),
        (RATE_LIMIT, 'rate limit'),
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active_before = models.DateTimeField()
    reason = models.CharField(null=False, choices=REASONS, max_length=64)
    group = models.ForeignKey('posting.Group', on_delete=models.CASCADE, null=False)

    def activate(self, group, reason, period_in_hours):
        fields = ['reason', 'active_before', 'is_active', 'group']
        now = timezone.now()

        self.active_before = now + timedelta(hours=period_in_hours)
        self.reason = reason
        self.group = group
        self.is_active = True

        self.save(update_fields=fields)

    def deactivate(self):
        fields = ['is_active']

        self.is_active = False

        self.save(update_fields=fields)

    def check_for_deactivation(self):
        need_deactivation = False

        if self.is_active and timezone.now() >= self.active_before:
            need_deactivation = True
            self.deactivate()

        return need_deactivation

    def __str__(self):
        return \
            f'Block {self.id} {self.is_active is True} for group {self.group} before {self.active_before}'

    def __repr__(self):
        return \
            f'Block {self.id} {self.is_active is True} for group {self.group} before {self.active_before}'

    class Meta:
        verbose_name = 'Блокировка'
        verbose_name_plural = 'Блокировки'

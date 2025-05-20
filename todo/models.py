import uuid

from django.db import models
from django.urls import reverse
from django.conf import settings

from .fields import OrderField


class DailyList(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=False,
    )
    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
    )
    created = models.DateField(
        auto_now_add=True,
    )
    updated = models.DateTimeField(
        auto_now=True,
    )
    notes = models.TextField(
        blank=True,
        default='',
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'daily list'
        verbose_name_plural = 'daily lists'

    def __str__(self):
        return f'{self.owner.username}: {self.created}'

    def get_absolute_url(self):
        return reverse('daily_task', args=[str(self.uid)])


class Task(models.Model):
    daily_list = models.ForeignKey(
        DailyList,
        on_delete=models.CASCADE,
        related_name='tasks',
        related_query_name='task',
    )
    description = models.CharField(
        max_length=250,
        blank=False,
    )
    completed = models.BooleanField(
        default=False,
        editable=True,
        null=False,
    )
    order = OrderField(
        blank=True,
        for_fields=['daily_list'],
    )

    class Meta:
        ordering = ('order',)
        verbose_name = 'task'
        verbose_name_plural = 'tasks'

    def __str__(self):
        return str(self.description)

import uuid
import datetime as dt

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone as django_timezone

from todo.fields import OrderField


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,

    )

    preferred_timezone = models.CharField(
        max_length=50,
        blank=False,
        default='America/Denver',
        editable=True,
    )

    def __str__(self):
        return f'Profile of {self.user.username}'


class DailyList(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=True,
        blank=True,
        null=True,
    )
    uid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
    )
    reference_timezone = models.CharField(
        max_length=50,
        default='America/Denver',  # b/c it's my tz =)
        blank=False,
        editable=True,
    )
    # created_dt, day_end_dt, locked_dt are timezone aware
    created_dt: dt.datetime = models.DateTimeField(
        auto_now_add=True,
        help_text='UTC datetime of list creation',
    )
    day_end_dt: dt.datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text='UTC datetime representing end of day in reference_timezone',
    )
    locked_dt: dt.datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text='UTC datetime representing when user can no longer edit list',
    )
    notes = models.TextField(
        blank=True,
        default='',
    )
    # todo: implement shareable logic
    shareable = models.BooleanField(
        default=False,
        blank=False,
        null=False,
        editable=True,
        help_text='True if unauthenticated users can view',
    )

    class Meta:
        ordering = ('-created_dt',)
        verbose_name = 'daily list'
        verbose_name_plural = 'daily lists'

    def __str__(self):
        return f'{self.owner}: {self.created_dt}'

    def get_absolute_url(self):
        return reverse('daily_list', args=[str(self.uid)])

    @property
    def completed_percentage(self) -> int:
        num_tasks = self.tasks.count()
        if num_tasks == 0:
            res = 0
        else:
            num_completed = self.tasks.filter(completed=True).count()
            res = int(100 * num_completed / num_tasks)
        return res

    @property
    def can_edit(self) -> bool:
        """True if aware datetime.now() is < self.locked_dt if locked_dt else True"""
        return django_timezone.now() < self.locked_dt if self.locked_dt else True


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
        ordering = ('-order',)
        verbose_name = 'task'
        verbose_name_plural = 'tasks'

    def __str__(self):
        return (
            f'{self.daily_list.created_dt}: '
            f'[{"x" if self.completed else ""}] '
            f'{self.description[:50]}'
            f'{"..." if len(self.description)>50 else ""}'
        )

    def toggle_completed(self):
        self.completed = not self.completed
        self.save()

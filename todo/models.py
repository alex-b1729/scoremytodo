import uuid
import datetime as dt

from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.core.validators import ValidationError

from todo.fields import OrderField


class DailyList(models.Model):
    # todo: need to update timezone logic!
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
    created: dt.datetime = models.DateTimeField(
        auto_now_add=True,
    )
    effective_date: dt.date = models.DateField(
        # todo dt.date.today is naive. Make aware
        default=dt.date.today,
        blank=False,
        null=False,
        editable=True,
    )
    notes = models.TextField(
        blank=True,
        default='',
    )
    shareable = models.BooleanField(
        default=False,
        blank=False,
        null=False,
        editable=True,
    )

    class Meta:
        ordering = ('-created',)
        verbose_name = 'daily list'
        verbose_name_plural = 'daily lists'

    def __str__(self):
        return f'{self.owner}: {self.effective_date}'

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
        """True if now() is < 12 hours after end of effective_date"""
        return (dt.datetime.now() - dt.timedelta(hours=12)).date() <= self.effective_date

    @property
    def can_move_effective_date_back(self) -> bool:
        """effective_date can be at most one day behind created date"""
        return self.effective_date >= self.created.date()

    @property
    def can_move_effective_date_forward(self) -> bool:
        """effective_date can be at most one day ahead of created date"""
        return self.effective_date <= self.created.date()

    @property
    def effective_date_is_valid(self) -> bool:
        """effective_date can be +/- 1 day of created date"""
        return abs(self.created.date() - self.effective_date) <= dt.timedelta(days=1)

    def move_effective_date_back(self):
        if self.can_move_effective_date_back:
            self.effective_date -= dt.timedelta(days=1)
            self.save()
        else:
            raise ValidationError("Effective date can be at most 1 day behind created date")

    def move_effective_date_forward(self):
        if self.can_move_effective_date_forward:
            self.effective_date += dt.timedelta(days=1)
            self.save()
        else:
            raise ValidationError("Effective date can be at most 1 day ahead of created date")


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
            f'{self.daily_list.created}: '
            f'[{"x" if self.completed else ""}] '
            f'{self.description[:50]}'
            f'{"..." if len(self.description)>50 else ""}'
        )

    def toggle_completed(self):
        self.completed = not self.completed
        self.save()

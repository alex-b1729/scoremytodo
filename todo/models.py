import uuid

from django.db import models
from django.urls import reverse
from django.conf import settings

from todo.fields import OrderField


class DailyList(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        editable=False,
        blank=True,
        null=True,
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
        return f'{self.owner}: {self.created}'

    def get_absolute_url(self):
        return reverse('daily_list', args=[str(self.uid)])

    @property
    def completed_percentage(self):
        num_tasks = self.tasks.count()
        if num_tasks == 0:
            res = 0
        else:
            num_completed = self.tasks.filter(completed=True).count()
            res = int(100 * num_completed / num_tasks)
        return res


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

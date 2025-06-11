import zoneinfo
import datetime as dt
from collections import defaultdict

import django.db.models.query
from django.db.models import Avg, IntegerField, Count
from django.db.models.functions import Trunc, Cast, Coalesce
from django.utils import timezone as django_timezone

from todo import models


"""
An eclectic mix of utility functions that deserve their own modules as they grow bigger. 
"""


def calculate_dailylist_datetimes_from_created_dt_and_timezone(
        created_dt: dt.datetime,
        reference_timezone: str,
) -> tuple[dt.datetime, dt.datetime]:
    """
    Given a DailyList.created_dt object in UTC and a timezone in zoneinfo.available_timezones()
    returns the end of day and datetime of the next calendar day at noon in timezone
    converted to UTC.
    If reference_timezone is not a recognized timezone the function returns 24 hours after
    created_dt for both values.
    :param created_dt: The timezone aware datetime that a DailyList object was created
    :param reference_timezone: A timezone in zoneinfo.available_timezones()
    :return: End of day in timezone, noon on the next calendar day in timezone, both converted to UTC
    """
    if reference_timezone not in zoneinfo.available_timezones():
        # this will either allow it to fail gracefully or will obscure bugs...
        return_dt = created_dt + dt.timedelta(hours=24)
        return return_dt, return_dt

    reference_tz_object = zoneinfo.ZoneInfo(reference_timezone)
    created_dt_in_tz = created_dt.astimezone(reference_tz_object)
    day_start_in_tz = created_dt_in_tz.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end_in_tz = day_start_in_tz + dt.timedelta(days=1)
    locked_dt_in_tz = day_end_in_tz + dt.timedelta(hours=12)

    day_end = day_end_in_tz.astimezone(dt.timezone.utc)
    locked_dt = locked_dt_in_tz.astimezone(dt.timezone.utc)

    return day_end, locked_dt


class TzRegionChoices:
    def __init__(self):
        self.region_set = set(
            reg.split('/')[0]
            for reg in zoneinfo.available_timezones()
        )
        self.regions = ((reg, reg) for reg in sorted(self.region_set))


class TzLocationChoices:
    def __init__(self):
        self.region2location = defaultdict(list)
        for tz in zoneinfo.available_timezones():
            tz_split = tz.split('/')
            self.region2location[tz_split[0]].append('/'.join(tz_split[1:]))

    def __getitem__(self, item):
        return ((loc, loc) for loc in sorted(self.region2location[item]) if loc != '')


def get_user_dailylist_score(
        user,
        days_back: int = 365,
) -> django.db.models.query.QuerySet:
    dailylist_score = models.DailyList.objects.filter(
        owner=user,
        created_dt__gt=(django_timezone.now() - dt.timedelta(days=days_back)),
    ).annotate(
        score=Coalesce(
            Avg(Cast('task__completed', IntegerField())),
            0.0,
        ),
        task_count=Count('task'),
    ).filter(task_count__gt=0).values_list('created_dt', 'score', named=True)
    return dailylist_score

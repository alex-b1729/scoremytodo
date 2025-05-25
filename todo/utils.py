import zoneinfo
import datetime as dt


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

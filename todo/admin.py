from django.contrib import admin

from .models import (
    DailyList,
    Task,
)


admin.site.register(DailyList)
admin.site.register(Task)

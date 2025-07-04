"""
URL configuration for scoremytodo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path

from todo import views as todo_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', todo_views.register, name='register'),
    path(
        'account/',
        include([
            path('', todo_views.account, name='account'),
            path('', include('django.contrib.auth.urls')),
            path('delete/', todo_views.account_delete, name='account_delete'),
            path(
                'select-timezone/',
                todo_views.SelectAccountTimezoneView.as_view(),
                name='account_select_timezone'
            ),
        ])
    ),
    path(
        'dashboard/',
        include([
            path('', todo_views.dashboard, name='dashboard'),
            path('score-data/', todo_views.score_data, name='score_data'),
        ])
    ),
    path('select-timezone/locations/', todo_views.load_location_form, name='load_location_form'),
    path(
        'todo/',
        include([
            # todays_list redirects to a new or current list for today
            path('', todo_views.TodaysList.as_view(), name='todays_list'),
            re_path(
                r'^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<date>[0-9]{2})/',
                todo_views.daily_list_by_date,
                name='daily_list_by_date'
            ),
            path(
                '<uuid:uid>/',
                include([
                    path('', todo_views.DailyListView.as_view(), name='daily_list'),
                    path('notes-edit/', todo_views.DailyListUpdateNotesView.as_view(), name='notes_edit'),
                    path('delete/', todo_views.daily_list_delete, name='daily_list_delete'),
                    path(
                        'select-timezone/',
                        todo_views.SelectDailyListTimezoneView.as_view(),
                        name='daily_list_select_timezone'
                    ),
                    re_path(r'^(?P<direction>previous|next)/$', todo_views.change_dailylist, name='change_daily_list'),
                    path(
                        'task/',
                        include([
                            path('create/', todo_views.TaskCreateUpdateView.as_view(), name='task_create'),
                            path('order/', todo_views.TaskOrderView.as_view(), name='task_order'),
                            path(
                                '<int:pk>/',
                                include([
                                    path('edit/', todo_views.TaskCreateUpdateView.as_view(), name='task_edit'),
                                    path('delete/', todo_views.task_delete, name='task_delete'),
                                    path('toggle/', todo_views.task_toggle, name='task_toggle'),
                                ])
                            )
                        ])
                    ),
                ])
            ),
        ])
    ),
    path('', todo_views.index, name='index'),
]

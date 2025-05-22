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
from django.urls import path, include
from django.contrib.auth import urls

from todo import views as todo_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', todo_views.register, name='register'),
    path(
        'accounts/',
        include([
            path('', todo_views.account, name='account'),
            path('', include('django.contrib.auth.urls')),
            path('delete/', todo_views.account_delete, name='account_delete')
        ])
    ),
    path('dashboard/', todo_views.dashboard, name='dashboard'),
    path(
        'todo/',
        include([
            # todays_list redirects to a new or current list for today
            path('', todo_views.TodaysList.as_view(), name='todays_list'),
            path(
                '<uuid:uid>/',
                include([
                    path('', todo_views.DailyListView.as_view(), name='daily_list'),
                    path('delete/', todo_views.daily_list_delete, name='daily_list_delete'),
                    path(
                        'task/',
                        include([
                            path('create/', todo_views.TaskCreateUpdateView.as_view(), name='task_create'),
                            path(
                                '<int:pk>/',
                                include([
                                    path('edit/', todo_views.TaskCreateUpdateView.as_view(), name='task_edit'),
                                    path('delete/', todo_views.task_delete, name='task_delete'),
                                    path('toggle/', todo_views.task_toggle, name='task_toggle'),
                                ])
                            )
                        ])
                    )
                ])
            ),
        ])
    ),
    path('', todo_views.index, name='index'),
]

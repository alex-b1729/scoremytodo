import datetime as dt

from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, reverse, get_object_or_404

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.views import generic
from django.views.generic.base import TemplateResponseMixin, View

from todo import forms
from todo import models


def index(request):
    return render(
        request,
        'index.html',
    )


def register(request):
    if request.method == 'POST':
        form = forms.UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            messages.success(request, f'Welcome, {new_user.username}.')
            return render(
                request,
                'dashboard.html',
            )
    else:
        form = forms.UserRegistrationForm()
    return render(
        request,
        'registration/register.html',
        {'form': form}
    )


@login_required
def account(request):
    return render(
        request,
        'account.html',
    )


@login_required
def account_delete(request):
    return render(
        request,
        'account_delete.html',
    )


@login_required
def dashboard(request):
    return render(
        request,
        'dashboard.html',
    )


class TodaysList(View):
    """Redirects to today's daily list or creates a new one"""

    daily_list = None
    created: bool

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # retrieve users td for today or create a new one
            self.daily_list, self.created = models.DailyList.objects.get_or_create(
                owner=request.user,
                created=dt.date.today(),
            )
        else:
            self.created = True
            self.daily_list = models.DailyList.objects.create(
                owner=None,
                shareable=True,
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.created:
            messages.success(request, f'New todo list created')
        else:
            messages.success(request, f'Continue with today\'s todo')
        return HttpResponseRedirect(
            reverse('daily_list', kwargs={'uid': self.daily_list.uid})
        )


class DailyListView(generic.TemplateView):
    template_name = 'daily_list.html'

    dailylist = None
    form = None

    def get_form(self):
        return forms.TaskEditForm()

    def dispatch(self, request, *args, **kwargs):
        self.dailylist = None
        self.form = None
        obj = get_object_or_404(
            models.DailyList,
            uid=kwargs.get('uid'),
        )
        if (obj.owner == self.request.user) or obj.shareable:
            self.dailylist = obj
        else:
            messages.warning(self.request, 'You can\'t view that todo')
            return HttpResponseRedirect(reverse('todays_list'))

        if not self.dailylist.tasks.exists():
            self.form = self.get_form()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'dailylist': self.dailylist,
            'form': self.form,
        })
        return context


@login_required
def daily_list_delete(request):
    if request.method == 'POST':
        print('deleted or something...')
    else:
        pass
    return render(
        request,
        'daily_list_delete.html',
        {'form': None}
    )


class TaskCreateUpdateView(View):
    dailylist = None
    task = None
    form = None

    def get_form(self, data=None, files=None):
        return forms.TaskEditForm(
            instance=self.task,
            data=data,
        )

    def dispatch(self, request, *args, **kwargs):
        self.dailylist = None
        self.task = None
        self.form = None

        # get the daily list the task is part of
        dailylist_uid = kwargs.get('uid')
        self.dailylist = get_object_or_404(
            models.DailyList,
            uid=dailylist_uid,
        )
        # don't allow editing of non-shared dailylists that you're not owner of
        if (self.dailylist.owner != request.user) and not self.dailylist.shareable:
            raise Http404

        # get task if exists
        task_pk = kwargs.get('pk')
        if task_pk:
            self.task = get_object_or_404(
                models.Task,
                pk=task_pk,
                daily_list=self.dailylist,
            )

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        return render(
            request,
            'partials/task_edit.html',
            {
                'form': self.form,
                'dailylist_uid': self.dailylist.uid,
            },
        )

    def post(self, request, *args, **kwargs):
        self.form = self.get_form(data=request.POST)
        if self.form.is_valid():
            updated_task = self.form.save(commit=False)
            if updated_task.pk:
                # editing existing
                updated_task.save()
            else:
                updated_task.daily_list = self.dailylist
                updated_task.save()
            return render(
                request,
                'partials/task_table_row.html',
                {'task': updated_task},
            )
        return render(
            request,
            'partials/task_edit.html',
            {
                'form': self.form,
                'dailylist_uid': self.dailylist.uid,
            },
        )

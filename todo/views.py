import datetime as dt

from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import render, reverse, get_object_or_404

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.views import generic
from django.views.decorators.http import require_POST
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

    def dispatch(self, request, *args, **kwargs):
        self.dailylist = None
        obj = get_object_or_404(
            models.DailyList,
            uid=kwargs.get('uid'),
        )
        if (obj.owner == self.request.user) or obj.shareable:
            self.dailylist = obj
        else:
            messages.warning(self.request, 'You can\'t view that todo')
            return HttpResponseRedirect(reverse('todays_list'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'dailylist': self.dailylist,
            'form': forms.TaskEditForm(),
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


@require_POST
@login_required
def daily_list_day_move(request, uid: str, direction: str):
    dailylist = get_object_or_404(
        models.DailyList,
        owner=request.user,
        uid=uid,
    )
    dir_multiple = -1 if direction == 'back' else 1
    # check if previous user already has a list associated with that day
    check_dl = models.DailyList.objects.filter(
        owner=request.user,
        effective_date=(dailylist.effective_date + dt.timedelta(days=1) * dir_multiple)
    )
    return_dl = None
    if check_dl.exists():
        # view returns check_dl if it exists and has associated tasks
        # note: could cause odd behavior since checks *first* qs result but deletes all
        if check_dl.first().tasks.exists():
            return_dl = check_dl.first()
        else:
            # delete check_dl since no associated tasks
            check_dl.delete()

    if not return_dl:
        # if a dailylist with the requested date doesn't exist or has no associated tasks
        # move the date of this dailylist to requested date
        if direction == 'back':
            dailylist.move_effective_date_back()
            return_dl = dailylist
        elif direction == 'forward':
            dailylist.move_effective_date_forward()
            return_dl = dailylist
    return HttpResponseRedirect(
            reverse('daily_list', kwargs={'uid': return_dl.uid})
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
                return render(
                    request,
                    'partials/task_table_row.html',
                    {
                        'task': updated_task,
                    },
                )
            else:
                # created new
                updated_task.daily_list = self.dailylist
                updated_task.save()
                return render(
                    request,
                    'partials/new_task_table_row.html',
                    {
                        'task': updated_task,
                        'form': self.get_form(),
                        'dailylist_uid': self.dailylist.uid,
                    },
                )
        # non-valid form
        return render(
            request,
            'partials/task_edit.html',
            {
                'form': self.form,
                'dailylist_uid': self.dailylist.uid,
            },
        )

# todo verify ownership before allowing editing!
@login_required
@require_POST
def task_delete(request, pk: int, uid: str):
    task = get_object_or_404(
        models.Task,
        pk=pk,
        daily_list__uid=uid,
    )
    task.delete()
    return render(
        request,
        'partials/progress_bar.html',
        {
            'completed_percentage': task.daily_list.completed_percentage,
        }
    )


@login_required
@require_POST
def task_toggle(request, pk: int, uid: str):
    task = get_object_or_404(
        models.Task,
        pk=pk,
        daily_list__uid=uid,
    )
    task.toggle_completed()
    return render(
        request,
        'partials/task_table_row_toggle_update.html',
        {
            'task': task,
            'completed_percentage': task.daily_list.completed_percentage,
        },
    )

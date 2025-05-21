import datetime as dt

from django.http import HttpResponse, HttpResponseRedirect
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
        print('dispatching todayslist')
        if request.user.is_authenticated:
            print('user authenticated')
            # retrieve users td for today or create a new one
            self.daily_list, self.created = models.DailyList.objects.get_or_create(
                owner=request.user,
                created=dt.date.today(),
            )
        else:
            print('user not auth, creating new list')
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
            uid=kwargs['uid'],
        )
        if (obj.owner == self.request.user) or obj.shareable:
            print('request user can view')
            self.dailylist = obj
        else:
            print('redirecting to new')
            # todo should make explicit to user that they can't view the list they queried
            messages.warning(self.request, 'You can\'t view that todo')
            return HttpResponseRedirect(reverse('todays_list'))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'dailylist': self.dailylist,
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

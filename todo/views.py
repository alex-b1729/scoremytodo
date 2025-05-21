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
    """Redirects a user's daily list or creates a new one"""

    daily_list = None

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # retrieve users td for today or create a new one
            daily_list, created = models.DailyList.objects.get_or_create(
                owner=request.user,
                created=dt.date.today(),
            )
            return HttpResponseRedirect(
                reverse('daily_list', kwargs={'uid': daily_list.uid})
            )
        else:
            return HttpResponse('no auth')


class DailyListView(generic.DetailView):
    model = models.DailyList
    context_object_name = 'daily_list'
    template_name = 'daily_list.html'

    def dispatch(self, request, *args, **kwargs):
        self.daily_list = get_object_or_404(
            models.DailyList,
            owner=request.user,
            uid=kwargs['uid'],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(daily_list=self.daily_list)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'daily_list': self.daily_list,
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

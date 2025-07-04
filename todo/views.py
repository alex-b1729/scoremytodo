import zoneinfo
import datetime as dt
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin

from django.http import (
    Http404,
    HttpResponse,
    JsonResponse,
    HttpResponseRedirect,
)
from django.shortcuts import render, reverse, get_object_or_404, redirect

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.views import generic
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateResponseMixin, View

from django.utils import timezone as django_timezone

from . import utils
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
            models.Profile.objects.create(user=new_user)
            new_user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            login(request, new_user)
            messages.success(request, f'Welcome, {new_user.username}.')
            return redirect('todays_list')
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


def get_or_create_user_dailylist(
        user: User,
) -> tuple[models.DailyList, bool]:
    """
    Given user either returns the DailyList associate with the user's current date if it exists
    or creates a new DailyList object. Second returned value is bool indicating if new object was created.
    :param user: The django user object
    :return: DailyList object and bool indicating if the object is new
    """
    # check for existing DailyList object where end of day is greater than now
    # note all the db timestamps are UTC
    existing_dl_qs = models.DailyList.objects.filter(
        owner=user,
        day_end_dt__gt=django_timezone.now(),
    )
    # return if exists
    # assumes there's only 1 object returned
    if existing_dl_qs.exists():
        return existing_dl_qs.first(), False

    # otherwise create new dailylist for user
    # get user's preferred timezone
    pref_tz = user.profile.preferred_timezone
    # init dailylist using preferred timezone
    new_dl = models.DailyList(
        owner=user,
        reference_timezone=pref_tz,
    )
    new_dl.save()
    day_end_dt, locked_dt = utils.calculate_dailylist_datetimes_from_created_dt_and_timezone(
        created_dt=new_dl.created_dt,
        reference_timezone=pref_tz,
    )
    new_dl.day_end_dt = day_end_dt
    new_dl.locked_dt = locked_dt
    new_dl.save()

    return new_dl, True


class TodaysList(
    LoginRequiredMixin,
    View,
):
    """Redirects to today's daily list or creates a new one"""

    def get(self, request, *args, **kwargs):
        daily_list, created = get_or_create_user_dailylist(request.user)
        if created:
            messages.success(request, f'New todo list created')
        return HttpResponseRedirect(
            reverse('daily_list', kwargs={'uid': daily_list.uid})
        )


class DailyListView(
    LoginRequiredMixin,
    generic.TemplateView,
):
    template_name = 'daily_list.html'

    dailylist: models.DailyList

    def dispatch(self, request, *args, **kwargs):
        self.dailylist = get_object_or_404(
            models.DailyList,
            owner=request.user,
            uid=kwargs.get('uid'),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'dailylist': self.dailylist,
            'form': forms.TaskEditForm(),
        })
        if self.dailylist.day_end_dt >= django_timezone.now():
            context.update({
                'section': 'today',
            })
        return context


@login_required
def daily_list_delete(request):
    # todo make work
    if request.method == 'POST':
        print('deleted or something...')
    else:
        pass
    return render(
        request,
        'daily_list_delete.html',
        {'form': None}
    )


class TaskCreateUpdateView(
    LoginRequiredMixin,
    View,
):
    dailylist: models.DailyList
    task: models.Task
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
            owner=request.user,
            uid=dailylist_uid,
        )

        # cannot add / edit tasks after day end
        if not self.dailylist.can_create_update_tasks:
            return JsonResponse(
                {
                    'error': 'Todo list is locked',
                    'message': 'Todo lists cannot be edited past midnight',
                },
                status=423,
            )

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
            'partials/task/edit.html',
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
                    'partials/task/table_row.html',
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
                    'partials/task/new_table_row.html',
                    {
                        'task': updated_task,
                        'completed_count': self.dailylist.completed_count,
                        'total_count': self.dailylist.tasks.count(),
                        'form': self.get_form(),
                        'dailylist_uid': self.dailylist.uid,
                    },
                )
        # non-valid form
        return render(
            request,
            'partials/task/edit.html',
            {
                'form': self.form,
                'dailylist_uid': self.dailylist.uid,
            },
        )


@login_required
@require_POST
def task_delete(request, pk: int, uid: str):
    task = get_object_or_404(
        models.Task,
        pk=pk,
        daily_list__owner=request.user,
        daily_list__uid=uid,
    )

    # cannot delete tasks after dailylist is locked
    if not task.can_create_or_update:
        return JsonResponse(
            {
                'error': 'Todo list is locked',
                'message': 'Todo list tasks cannot be edited past midnight',
            },
            status=423,
        )

    task.delete()
    return render(
        request,
        'partials/task/delete.html',
        {
            'completed_count': task.daily_list.completed_count,
            'total_count': task.daily_list.tasks.count(),
            'completed_percentage': task.daily_list.completed_percentage,
        }
    )


@login_required
@require_POST
def task_toggle(request, pk: int, uid: str):
    task = get_object_or_404(
        models.Task,
        pk=pk,
        daily_list__owner=request.user,
        daily_list__uid=uid,
    )

    # cannot checkoff tasks past dailylist.locked_dt
    if not task.can_checkoff:
        return JsonResponse(
            {
                'error': 'Todo list is locked',
                'message': 'Todo list tasks cannot be checked off after noon the next day',
            },
            status=423,
        )

    task.toggle_completed()
    return render(
        request,
        'partials/task/table_row_toggle_update.html',
        {
            'task': task,
            'completed_count': task.daily_list.completed_count,
            'total_count': task.daily_list.tasks.count(),
            'completed_percentage': task.daily_list.completed_percentage,
        },
    )


@login_required
def load_location_form(request):
    region = request.GET.get('region-region')
    if region:
        if region not in utils.TzRegionChoices().region_set:
            return Http404
    else:
        region = 'America'
    location_form = forms.UserTzLocationForm(
        region=region,
        prefix='location',
    )
    return render(
        request,
        'partials/tz/location_select.html',
        {
            'location_form': location_form,
        }
    )


class SelectTimezoneView(
    LoginRequiredMixin,
    TemplateResponseMixin,
    View,
):
    template_name = 'select_timezone.html'
    region_form = None
    location_form = None
    init_region: str
    init_location: str
    selected_region: str
    selected_location: str
    selected_tz: str

    def set_region_form(self, data=None, files=None):
        self.region_form = forms.UserTzRegionForm(
            data=data,
            initial={'region': self.init_region},
            prefix='region',
        )

    def set_location_form(self, region: str, data=None, files=None):
        self.location_form = forms.UserTzLocationForm(
            data=data,
            region=region,
            initial={'location': self.init_location},
            prefix='location',
        )

    def dispatch(self, request, *args, **kwargs):
        self.get_initial_tz_or_set_default(request)
        return super().dispatch(request, *args, **kwargs)

    def get_initial_tz_or_set_default(self, request):
        self.init_region = request.GET.get('region')
        self.init_location = request.GET.get('location')

        if not self.init_region and not self.init_location:
            # neither defined => set default
            self.init_region = 'America'
            self.init_location = 'Denver'
        elif self.init_region and not self.init_location:
            if self.init_region not in utils.TzRegionChoices().region_set:
                self.init_region = 'America'
        elif not self.init_region and self.init_location:
            # can't specify init_location w/o init_region
            self.init_region = 'America'
            self.init_location = 'Denver'
        else:
            # both init_region, init_location are defined
            if self.init_region not in utils.TzRegionChoices().region_set:
                self.init_region = 'America'
            else:
                if self.init_location not in utils.TzLocationChoices().region2location[self.init_region]:
                    # ignore init_location if not part of init_region
                    self.init_location = 'Denver'

    def get(self, request, *args, **kwargs):
        self.set_region_form()
        self.set_location_form(region=self.init_region)
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.set_region_form(data=request.POST)
        self.selected_region = None
        if self.region_form.is_valid():
            # user's selected region
            self.selected_region = self.region_form.cleaned_data['region']

            self.set_location_form(region=self.selected_region, data=request.POST)
            self.selected_location = None
            if self.location_form.is_valid():
                # user's selected location
                self.selected_location = self.location_form.cleaned_data['location']

                self.selected_tz = (f'{self.selected_region}'
                                    f'{"/" + self.selected_location if self.selected_location else ""}')
                return self.post_success()
        return self.render_to_response(self.get_context_data())

    def get_context_data(self):
        return {
            'region_form': self.region_form,
            'location_form': self.location_form,
        }

    def post_success(self):
        """
        Returned by self.post() if all forms are valid.
        Override on child classes to process self.selected_tz as appropriate.
        Don't forget to return something.
        """
        return HttpResponse(f'selected tz is {self.selected_tz}!')


class SelectDailyListTimezoneView(SelectTimezoneView):
    template_name = 'partials/tz/select_timezone.html'
    dailylist: models.DailyList

    def dispatch(self, request, *args, **kwargs):
        self.dailylist = get_object_or_404(
            models.DailyList,
            owner=request.user,
            uid=kwargs.get('uid'),
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial_tz_or_set_default(self, request):
        current_tz = str(self.dailylist.reference_timezone).split('/')
        self.init_region = current_tz[0]
        self.init_location = '/'.join(current_tz[1:])

    def get_context_data(self):
        context = super().get_context_data()
        context.update({
            'post_target': reverse(
                'daily_list_select_timezone',
                kwargs={'uid': self.dailylist.uid}
            ),
            'cancel_url': self.dailylist.get_absolute_url(),
        })
        return context

    def post_success(self):
        self.dailylist.reference_timezone = self.selected_tz
        self.dailylist.save()
        messages.success(self.request, f'Todo timezone updated')
        return HttpResponseRedirect(self.dailylist.get_absolute_url())


class SelectAccountTimezoneView(SelectTimezoneView):
    template_name = 'partials/tz/select_timezone.html'
    profile: models.Profile

    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(
            models.Profile,
            user=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def get_initial_tz_or_set_default(self, request):
        current_tz = str(self.profile.preferred_timezone).split('/')
        self.init_region = current_tz[0]
        self.init_location = '/'.join(current_tz[1:])

    def get_context_data(self):
        context = super().get_context_data()
        context.update({
            'post_target': reverse('account_select_timezone'),
            'cancel_url': self.profile.get_absolute_url(),
        })
        return context

    def post_success(self):
        self.profile.preferred_timezone = self.selected_tz
        self.profile.save()
        messages.success(self.request, f'Profile timezone updated')
        return HttpResponseRedirect(self.profile.get_absolute_url())


@login_required
def dashboard(request):
    return render(
        request,
        'dashboard.html',
        {
            'section': 'dashboard',
        }
    )


@login_required
def score_data(request):
    dailylist_score_qs = utils.get_user_dailylist_score(user=request.user)
    user_tz = zoneinfo.ZoneInfo(request.user.profile.preferred_timezone)

    processed_data = []

    # todo i'd rather not loop through the values but for now
    for item in dailylist_score_qs:
        user_tz_timestamp = item.created_dt.astimezone(user_tz).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).strftime('%Y-%m-%d')

        score = int(item.score * 100)
        processed_data.append({
            'date': user_tz_timestamp,
            'score': score,
        })

    return JsonResponse({'data': processed_data})


@login_required
def change_dailylist(request, uid: str, direction: str):
    this_dailylist = get_object_or_404(
        models.DailyList,
        owner=request.user,
        uid=uid,
    )
    if direction == 'previous':
        return_dailylist = models.DailyList.objects.filter(
            owner=request.user,
            created_dt__lt=this_dailylist.created_dt,
        ).order_by('-created_dt').first()
    elif direction == 'next':
        return_dailylist = models.DailyList.objects.filter(
            owner=request.user,
            created_dt__gt=this_dailylist.created_dt,
        ).order_by('created_dt').first()
    else:
        return Http404()
    if not return_dailylist:
        messages.error(request, f'You do not have a {direction} todo list.')
        return_dailylist = this_dailylist
    return HttpResponseRedirect(
        reverse('daily_list', kwargs={'uid': return_dailylist.uid})
    )


@login_required
def daily_list_by_date(request, year: str, month: str, date: str):
    users_tz = zoneinfo.ZoneInfo(request.user.profile.preferred_timezone)
    try:
        requested_dt_user_tz = dt.datetime(int(year), int(month), int(date), tzinfo=users_tz)
    except ValueError:
        return Http404()

    requested_dt = requested_dt_user_tz.astimezone(dt.timezone.utc)
    print(requested_dt.date())

    dailylist = get_object_or_404(
        models.DailyList,
        owner=request.user,
        created_dt__date=requested_dt,
    )

    return HttpResponseRedirect(dailylist.get_absolute_url())


class DailyListUpdateNotesView(
    LoginRequiredMixin,
    View,
):
    dailylist: models.DailyList
    form = None

    def get_form(self, data=None, files=None):
        return forms.DailyListNotesForm(
            instance=self.dailylist,
            data=data,
        )

    def dispatch(self, request, *args, **kwargs):
        self.dailylist = None
        self.form = None

        # get the daily list the task is part of
        dailylist_uid = kwargs.get('uid')
        self.dailylist = get_object_or_404(
            models.DailyList,
            owner=request.user,
            uid=dailylist_uid,
        )

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        return render(
            request,
            'partials/dailylist/notes_edit.html',
            {
                'form': self.form,
            },
        )

    def post(self, request, *args, **kwargs):
        self.form = self.get_form(data=request.POST)
        if self.form.is_valid():
            updated_dailylist = self.form.save()
            return render(
                request,
                'partials/dailylist/notes.html',
                {
                    'notes': updated_dailylist.notes,
                    'dailylist_uid': updated_dailylist.uid,
                }
            )
        # non-valid form
        return render(
            request,
            'partials/dailylist/notes_edit.html',
            {
                'form': self.form,
            },
        )


class TaskOrderView(
    CsrfExemptMixin,
    JsonRequestResponseMixin,
    View,
):
    def post(self, request, uid):
        for pk, order in self.request_json.items():
            t = models.Task.objects.get(
                pk=pk,
                daily_list__owner=request.user,
                daily_list__uid=uid,
            )
            models.Task.objects.filter(
                pk=pk,
                daily_list__owner=request.user,
                daily_list__uid=uid,
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})

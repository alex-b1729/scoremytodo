import zoneinfo

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation

from todo import models


TZ_DICT = dict()
for tz in zoneinfo.available_timezones():
    tz_split = tz.split('/')
    TZ_DICT[tz_split[0]].append('/'.join(tz_split[1:]).replace('_', ' '))


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    password2 = forms.CharField(
        label='Repeat password',
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )

    class Meta:
        model = get_user_model()
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'autocomplete': 'off'}),
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords do not match.")
        return cd['password2']

    def save(self, commit=True):
        user = super(UserRegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password2'])
        user.save(commit)
        return user


class TaskEditForm(forms.ModelForm):
    class Meta:
        model = models.Task
        fields = ('description',)
        widgets = {
            'daily_list': forms.HiddenInput,
            'description': forms.TextInput(attrs={
                'placeholder': 'New task',
                'class': 'form-control form-control-sm',
                'aria-label': 'New Task',
                'aria-describedby': 'button-addon',
                'autofocus': 'autofocus',
            })
        }


class UserTzFormPart1(forms.Form):
    pass

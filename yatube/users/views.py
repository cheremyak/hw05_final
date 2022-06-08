from django.contrib.auth.views import (PasswordChangeView,
                                       PasswordResetView,
                                       PasswordResetConfirmView)
from django.views.generic import CreateView
from django.urls import reverse_lazy

from .forms import CreationForm, PassChangeForm, PassResetForm, SetPassForm


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


class PasswordChange(PasswordChangeView):
    form_class = PassChangeForm
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_form.html'


class PasswordReset(PasswordResetView):
    form_class = PassResetForm
    success_url = reverse_lazy('users:password_reset_done')
    template_name = 'users/password_reset_form.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    form_class = SetPassForm
    success_url = reverse_lazy('users:password_reset_complete')
    template_name = 'users/password_reset_confirm.html'

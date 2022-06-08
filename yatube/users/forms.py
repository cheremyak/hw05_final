from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       SetPasswordForm, UserCreationForm)
from django.contrib.auth import get_user_model


User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class PassChangeForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')


class PassResetForm(PasswordResetForm):
    class Meta:
        model = User
        fields = ('email')


class SetPassForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ('new_password1', 'new_password2')

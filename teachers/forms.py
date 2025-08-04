from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Import constants
from utils.constant import (
    ADMIN_USERNAME_MAX_LENGTH,
    ADMIN_USERNAME_MIN_LENGTH,
    ADMIN_PASSWORD_MIN_LENGTH,
    FORM_CONTROL_CLASS,
    USERNAME_FIELD_ID,
    PASSWORD_FIELD_ID,
    REQUIRED_ATTRIBUTE,
    ADMIN_USERNAME_MIN_LENGTH_ERROR,
    ADMIN_PASSWORD_MIN_LENGTH_ERROR,
    ADMIN_INVALID_CREDENTIALS_ERROR,
    ADMIN_INACTIVE_ACCOUNT_ERROR,
    USERNAME_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    USERNAME_LABEL,
    PASSWORD_LABEL,
)

# Import models
from admins.models import User
from teachers.models import Teacher


class TeacherLoginForm(forms.Form):
    """
    Teacher login form with data validation and cleaning
    """
    username = forms.CharField(
        max_length=ADMIN_USERNAME_MAX_LENGTH,
        widget=forms.TextInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'id': USERNAME_FIELD_ID,
            'placeholder': _(USERNAME_PLACEHOLDER),
            'required': REQUIRED_ATTRIBUTE
        }),
        label=_(USERNAME_LABEL)
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': FORM_CONTROL_CLASS,
            'id': PASSWORD_FIELD_ID,
            'placeholder': _(PASSWORD_PLACEHOLDER),
            'required': REQUIRED_ATTRIBUTE
        }),
        label=_(PASSWORD_LABEL)
    )

    def __init__(self, request=None, *args, **kwargs):
        """
        Initialize form with request object for authentication
        """
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean_username(self):
        """
        Clean and validate username field
        """
        username = self.cleaned_data.get('username')
        if username:
            username = username.strip().lower()
            if len(username) < ADMIN_USERNAME_MIN_LENGTH:
                raise ValidationError(
                    _(ADMIN_USERNAME_MIN_LENGTH_ERROR.format(ADMIN_USERNAME_MIN_LENGTH)))
        return username

    def clean_password(self):
        """
        Clean and validate password field
        """
        password = self.cleaned_data.get('password')
        if password:
            if len(password) < ADMIN_PASSWORD_MIN_LENGTH:
                raise ValidationError(
                    _(ADMIN_PASSWORD_MIN_LENGTH_ERROR.format(ADMIN_PASSWORD_MIN_LENGTH)))
        return password

    def clean(self):
        """
        Validate the entire form and authenticate user
        """
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            # Authenticate user
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )

            if self.user_cache is None:
                raise ValidationError(_(ADMIN_INVALID_CREDENTIALS_ERROR))

            if not self.user_cache.is_active:
                raise ValidationError(_(ADMIN_INACTIVE_ACCOUNT_ERROR))

            # Check if user is a teacher
            if not self.user_cache.is_teacher:
                raise ValidationError(
                    _('You do not have permission to access the teacher area.'))

        return cleaned_data

    def get_user(self):
        """
        Return authenticated user
        """
        return self.user_cache
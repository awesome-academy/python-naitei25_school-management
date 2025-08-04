# Django imports
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext_lazy as _

# Local application imports
from utils.constant import (
    ADMIN_INVALID_CREDENTIALS_ERROR,
    ADMIN_INACTIVE_ACCOUNT_ERROR,
    ADMIN_USERNAME_MIN_LENGTH_ERROR,
    ADMIN_PASSWORD_MIN_LENGTH_ERROR,
    ADMIN_USERNAME_MIN_LENGTH,
    ADMIN_PASSWORD_MIN_LENGTH,
    FORM_CONTROL_CLASS,
    USERNAME_FIELD_ID,
    PASSWORD_FIELD_ID,
    REQUIRED_ATTRIBUTE,
    USERNAME_PLACEHOLDER,
    PASSWORD_PLACEHOLDER,
    USERNAME_LABEL,
    PASSWORD_LABEL,
    ADMIN_USERNAME_MAX_LENGTH,
)

# Import models
from admins.models import User
from students.models import Student
from teachers.models import Teacher

from django import forms
from django.core.exceptions import ValidationError


class UnifiedLoginForm(forms.Form):
    """
    Unified login form for all user types (admin, teacher, student)
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

        return cleaned_data

    def get_user(self):
        """
        Return authenticated user
        """
        return self.user_cache


@csrf_protect
def unified_login(request):
    """
    Unified login view that handles admin, teacher, and student login
    Auto-detects user role and redirects accordingly
    """
    # Check if user is already authenticated and redirect to appropriate dashboard
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_teacher:
            return redirect('teacher_dashboard')
        elif request.user.is_student:
            return redirect('student_dashboard')

    # Initialize form
    form = UnifiedLoginForm(request=request)

    if request.method == 'POST':
        form = UnifiedLoginForm(request, data=request.POST)

        if form.is_valid():
            # Get cleaned data and authenticated user
            user = form.get_user()

            # Login user
            login(request, user)
            
            # Determine user role and redirect accordingly
            if user.is_superuser:
                messages.success(
                    request,
                    _('Welcome {}! (Administrator)').format(
                        user.get_full_name() or user.username)
                )
                return redirect('admin_dashboard')
            elif user.is_teacher:
                messages.success(
                    request,
                    _('Welcome {}! (Teacher)').format(
                        user.get_full_name() or user.username)
                )
                return redirect('teacher_dashboard')
            elif user.is_student:
                messages.success(
                    request,
                    _('Welcome {}! (Student)').format(
                        user.get_full_name() or user.username)
                )
                return redirect('student_dashboard')
            else:
                # User exists but has no specific role
                logout(request)
                messages.error(request, _('Your account does not have access to this system.'))
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    context = {
        'form': form
    }
    return render(request, 'common/login.html', context)


def unified_logout(request):
    """
    Unified logout view for all user types
    """
    if request.user.is_authenticated:
        user_type = ""
        if request.user.is_superuser:
            user_type = " (Administrator)"
        elif request.user.is_teacher:
            user_type = " (Teacher)"
        elif request.user.is_student:
            user_type = " (Student)"
        
        messages.success(request, _('You have been logged out successfully{}').format(user_type))
    
    logout(request)
    return redirect('unified_login')
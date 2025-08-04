# Django imports
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext_lazy as _

# Local application imports
from utils.constant import (
    ADMIN_DATETIME_FORMAT,
    ADMIN_WELCOME_MESSAGE,
    ADMIN_LOGOUT_SUCCESS_MESSAGE
)
from .forms import TeacherLoginForm

# Model imports
from teachers.models import Teacher


@csrf_protect
def teacher_login(request):
    """
    Teacher login view with form validation and clean data
    """
    # Redirect authenticated teacher users
    if request.user.is_authenticated and request.user.is_teacher:
        return redirect('teacher_dashboard')

    # Initialize form
    form = TeacherLoginForm(request=request)

    if request.method == 'POST':
        form = TeacherLoginForm(request, data=request.POST)

        if form.is_valid():
            # Get cleaned data and authenticated user
            user = form.get_user()

            # Login user
            login(request, user)
            messages.success(
                request,
                _('Welcome {}!').format(
                    user.get_full_name() or user.username)
            )
            return redirect('teacher_dashboard')
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    context = {
        'form': form
    }
    return render(request, 'teachers/login.html', context)


@login_required
def teacher_dashboard(request):
    """
    Teacher dashboard view
    """
    # Check if user is teacher
    if not request.user.is_teacher:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('unified_login')

    # Get teacher instance
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, _('Teacher profile not found.'))
        return redirect('unified_login')

    context = {
        'teacher': teacher,
        'user': request.user,
        'date_format': ADMIN_DATETIME_FORMAT,
    }

    return render(request, 't_homepage.html', context)


def teacher_logout(request):
    """
    Teacher logout view
    """
    if request.user.is_authenticated and request.user.is_teacher:
        messages.success(request, _('You have been logged out successfully.'))
    logout(request)
    return redirect('unified_login')


# Alias for backwards compatibility
def index(request):
    """
    Legacy index view - redirect to dashboard
    """
    return redirect('teacher_dashboard')

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
)
from .forms import StudentLoginForm

# Model imports
from students.models import Student


@csrf_protect
def student_login(request):
    """
    Student login view with form validation and clean data
    """
    # Redirect authenticated student users
    if request.user.is_authenticated and request.user.is_student:
        return redirect('student_dashboard')

    # Initialize form
    form = StudentLoginForm(request=request)

    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)

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
            return redirect('student_dashboard')
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    context = {
        'form': form
    }
    return render(request, 'students/login.html', context)


@login_required
def student_dashboard(request):
    """
    Student dashboard view
    """
    # Check if user is student
    if not request.user.is_student:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('unified_login')

    # Get student instance
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, _('Student profile not found.'))
        return redirect('unified_login')

    context = {
        'student': student,
        'user': request.user,
        'date_format': ADMIN_DATETIME_FORMAT,
    }

    return render(request, 'students/dashboard.html', context)


def student_logout(request):
    """
    Student logout view
    """
    if request.user.is_authenticated and request.user.is_student:
        messages.success(request, _('You have been logged out successfully.'))
    logout(request)
    return redirect('unified_login')
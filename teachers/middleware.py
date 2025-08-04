from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect


class TeacherPermissionMiddleware:
    """
    Middleware to check teacher permissions for teacher area
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Teacher URLs that require authentication
        self.teacher_protected_urls = [
            '/teacher/dashboard/',
        ]
        # Teacher URLs that don't require authentication 
        self.teacher_public_urls = [
            '/teacher/login/',
            '/teacher/logout/',
            '/teacher/',  # redirects to login
        ]

    def __call__(self, request):
        # Check if request is for teacher area
        if request.path.startswith('/teacher/'):
            # Skip if it's a public URL
            if not any(request.path.startswith(url) for url in self.teacher_public_urls):
                # Check if user is authenticated
                if not request.user.is_authenticated:
                    messages.error(request, _('Please login to access the teacher area.'))
                    return HttpResponseRedirect(reverse('unified_login'))
                
                # Check if user is a teacher
                if not request.user.is_teacher:
                    messages.error(request, _('You do not have permission to access the teacher area.'))
                    return HttpResponseRedirect(reverse('unified_login'))

        response = self.get_response(request)
        return response
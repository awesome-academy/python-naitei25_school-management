from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect


class StudentPermissionMiddleware:
    """
    Middleware to check student permissions for student area
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Student URLs that require authentication
        self.student_protected_urls = [
            '/student/dashboard/',
        ]
        # Student URLs that don't require authentication 
        self.student_public_urls = [
            '/student/login/',
            '/student/logout/',
            '/student/',  # redirects to login
        ]

    def __call__(self, request):
        # Check if request is for student area
        if request.path.startswith('/student/'):
            # Skip if it's a public URL
            if not any(request.path.startswith(url) for url in self.student_public_urls):
                # Check if user is authenticated
                if not request.user.is_authenticated:
                    messages.error(request, _('Please login to access the student area.'))
                    return HttpResponseRedirect(reverse('unified_login'))
                
                # Check if user is a student
                if not request.user.is_student:
                    messages.error(request, _('You do not have permission to access the student area.'))
                    return HttpResponseRedirect(reverse('unified_login'))

        response = self.get_response(request)
        return response
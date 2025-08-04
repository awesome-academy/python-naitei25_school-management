from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.teacher_login, name='teacher_login'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('logout/', views.teacher_logout, name='teacher_logout'),
    # Redirect to login by default
    path('', views.teacher_login, name='teacher_home'),
    # Legacy route for compatibility
    path('index/', views.index, name='index'),
]

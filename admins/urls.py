from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('add-student/', views.add_student, name='add_student'),
    path('add-teacher/', views.add_teacher, name='add_teacher'),
    # Redirect to login by default
    path('', views.admin_login, name='admin_home'),
]

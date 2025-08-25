from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('add-student/', views.add_student, name='add_student'),
    path('add-teacher/', views.add_teacher, name='add_teacher'),

    # Teaching Assignment URLs
    path('teaching-assignments/', views.teaching_assignments, name='teaching_assignments'),
    path('teaching-assignments/add/', views.add_teaching_assignment, name='add_teaching_assignment'),
    path('teaching-assignments/<int:assignment_id>/edit/', views.edit_teaching_assignment, name='edit_teaching_assignment'),
    path('teaching-assignments/<int:assignment_id>/delete/', views.delete_teaching_assignment, name='delete_teaching_assignment'),
    
    # Timetable URLs
    path('timetable/', views.timetable, name='timetable'),
    path('timetable/add/', views.add_timetable_entry, name='add_timetable_entry'),
    path('timetable/<int:entry_id>/edit/', views.edit_timetable_entry, name='edit_timetable_entry'),
    path('timetable/<int:entry_id>/delete/', views.delete_timetable_entry, name='delete_timetable_entry'),
    
    # Redirect to login by default
    path('', views.admin_login, name='admin_home'),
    # Class URLs
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.add_class, name='add_class'),
    path('classes/<str:class_id>/edit/', views.edit_class, name='edit_class'),
    path('classes/<str:class_id>/delete/', views.delete_class, name='delete_class'),
    # CRUD học sinh
    path('classes/<str:class_id>/add-student/', views.add_student_to_class, name='add_student_to_class'),
    path('students/edit/<str:student_id>/', views.edit_student, name='edit_student'),
    path('students/delete/<str:student_id>/', views.delete_student, name='delete_student'),

     # Deparment URLs
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/<str:dept_id>/edit/', views.edit_department, name='edit_department'),
    path('departments/<str:dept_id>/delete/', views.delete_department, name='delete_department'),
    
    #Subjects URLs
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/<str:subject_id>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<str:subject_id>/delete/', views.delete_subject, name='delete_subject'),
    
    #Thêm subject vào class
    path('classes/<str:class_id>/add-subject/', views.add_subject_to_class, name='add_subject_to_class'),
    path('classes/<str:class_id>/remove-subject/<int:assign_id>/', views.remove_subject_from_class, name='remove_subject_from_class'),
    
    #Report admin
    path('reports/', views.admin_reports, name='admin_reports'),
    
    #Quản lý người dùng
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    
]

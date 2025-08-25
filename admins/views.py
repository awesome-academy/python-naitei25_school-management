# Django imports
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext_lazy as _
from admins.models import User
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Case, When, Value, IntegerField

# Local application imports
from utils.constant import (
    ADMIN_DATETIME_FORMAT,
    ADMIN_WELCOME_MESSAGE,
    ADMIN_LOGOUT_SUCCESS_MESSAGE,
    PAGE_SIZE, ZERO 
)
from .forms import (
    AdminLoginForm,
    AddStudentForm,
    AddTeacherForm,
    TeachingAssignmentForm,
    TeachingAssignmentFilterForm,
    TimetableFilterForm,
    TimetableForm,
    ClassForm,
    EditStudentForm,
    DepartmentForm,
    SubjectForm,
    AddSubjectToClassForm,
    AddUserForm,
    EditUserForm)
# Model imports
from students.models import Student, Attendance, StudentSubject, AttendanceTotal
from teachers.models import Teacher, Assign, AssignTime, Marks, ExamSession, AttendanceClass
from admins.models import User, Dept, Subject, Class


@csrf_protect
def admin_login(request):
    """
    Custom admin login view with form validation and clean data
    """
    # Redirect authenticated admin users
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')

    # Initialize form
    form = AdminLoginForm(request=request)

    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)

        if form.is_valid():
            # Get cleaned data and authenticated user
            user = form.get_user()

            # Login user
            login(request, user)
            messages.success(
                request,
                _(ADMIN_WELCOME_MESSAGE) % {
                    'name': user.get_full_name() or user.username}
            )
            return redirect('admin_dashboard')
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    context = {
        'form': form
    }
    return render(request, 'admins/login.html', context)


def admin_dashboard(request):
    """
    Admin dashboard view
    Note: Admin permission check is handled by AdminPermissionMiddleware
    """
    # Basic statistics
    context = {
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_departments': Dept.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_classes': Class.objects.count(),
        'admin_user': request.user,
        'date_format': ADMIN_DATETIME_FORMAT,
    }

    return render(request, 'admins/dashboard.html', context)


def admin_logout(request):
    """
    Admin logout view
    Note: Admin permission check is handled by AdminPermissionMiddleware
    """
    if request.user.is_authenticated and request.user.is_superuser:
        messages.success(request, _(ADMIN_LOGOUT_SUCCESS_MESSAGE))
    logout(request)
    return redirect('admin_login')


def add_student(request):
    """
    Add new student view
    Note: Admin permission check is handled by AdminPermissionMiddleware
    """
    if request.method == 'POST':
        form = AddStudentForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user account
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['name'].split()[0],
                        last_name=' '.join(form.cleaned_data['name'].split()[1:]) if len(
                            form.cleaned_data['name'].split()) > 1 else ''
                    )

                    # Create student profile
                    student = Student.objects.create(
                        user=user,
                        USN=form.cleaned_data['USN'],
                        name=form.cleaned_data['name'],
                        sex=form.cleaned_data['sex'],
                        DOB=form.cleaned_data['DOB'],
                        address=form.cleaned_data['address'],
                        phone=form.cleaned_data['phone'],
                        class_id=form.cleaned_data['class_id']
                    )

                    messages.success(request, _(
                        'Student "{}" has been successfully added.').format(student.name))
                    return redirect('admin_dashboard')

            except Exception as e:
                messages.error(request, _(
                    'Error creating student: {}').format(str(e)))
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = AddStudentForm()

    context = {
        'form': form,
        'title': _('Add Student'),
        'submit_text': _('Add Student'),
        'admin_user': request.user,
    }
    return render(request, 'admins/add_student.html', context)


def add_teacher(request):
    """
    Add new teacher view
    Note: Admin permission check is handled by AdminPermissionMiddleware
    """
    if request.method == 'POST':
        form = AddTeacherForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user account
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['name'].split()[0],
                        last_name=' '.join(form.cleaned_data['name'].split()[1:]) if len(
                            form.cleaned_data['name'].split()) > 1 else ''
                    )

                    # Create teacher profile
                    teacher = Teacher.objects.create(
                        user=user,
                        id=form.cleaned_data['id'],
                        name=form.cleaned_data['name'],
                        sex=form.cleaned_data['sex'],
                        DOB=form.cleaned_data['DOB'],
                        address=form.cleaned_data['address'],
                        phone=form.cleaned_data['phone'],
                        dept=form.cleaned_data['dept']
                    )

                    messages.success(request, _(
                        'Teacher "{}" has been successfully added.').format(teacher.name))
                    return redirect('admin_dashboard')

            except Exception as e:
                messages.error(request, _(
                    'Error creating teacher: {}').format(str(e)))
        else:
            # Form has validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = AddTeacherForm()

    context = {
        'form': form,
        'title': _('Add Teacher'),
        'submit_text': _('Add Teacher'),
        'admin_user': request.user,
    }
    return render(request, 'admins/add_teacher.html', context)


@login_required
def teaching_assignments(request):
    """
    View for managing teaching assignments
    """
    # Handle filter form
    filter_form = TeachingAssignmentFilterForm(request.GET)
    assignments = Assign.objects.all()

    if filter_form.is_valid():
        teacher = filter_form.cleaned_data.get('teacher')
        subject = filter_form.cleaned_data.get('subject')
        class_id = filter_form.cleaned_data.get('class_id')

        if teacher:
            assignments = assignments.filter(teacher=teacher)
        if subject:
            assignments = assignments.filter(subject=subject)
        if class_id:
            assignments = assignments.filter(class_id=class_id)

    # Pagination
    paginator = Paginator(assignments, PAGE_SIZE)  # 10 entries per page
    page_number = request.GET.get('page')
    assignments = paginator.get_page(page_number)

    context = {
        'assignments': assignments,
        'filter_form': filter_form,
        'admin_user': request.user,
    }
    return render(request, 'admins/teaching_assignments.html', context)


@login_required
@permission_required('assign.add_assign', raise_exception=True)
def add_teaching_assignment(request):
    """
    View for adding a new teaching assignment
    """
    if request.method == 'POST':
        form = TeachingAssignmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _(
                'Teaching assignment has been added successfully!'))
            return redirect('teaching_assignments')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = TeachingAssignmentForm()

    context = {
        'form': form,
        'admin_user': request.user,
        'title': _('Add Teaching Assignment')
    }
    return render(request, 'admins/teaching_assignment_form.html', context)


@login_required
@permission_required('assign.change_assign', raise_exception=True)
def edit_teaching_assignment(request, assignment_id):
    """
    View for editing a teaching assignment
    """
    try:
        assignment = Assign.objects.get(id=assignment_id)
    except Assign.DoesNotExist:
        messages.error(request, _('The teaching assignment does not exist!'))
        return redirect('teaching_assignments')

    if request.method == 'POST':
        form = TeachingAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, _(
                'Teaching assignment has been updated successfully!'))
            return redirect('teaching_assignments')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = TeachingAssignmentForm(instance=assignment)

    context = {
        'form': form,
        'assignment': assignment,
        'admin_user': request.user,
        'title': _('Edit Teaching Assignment')
    }
    return render(request, 'admins/teaching_assignment_form.html', context)


@login_required
@permission_required('assign.delete_assign', raise_exception=True)
def delete_teaching_assignment(request, assignment_id):
    """
    View for deleting a teaching assignment
    """
    try:
        assignment = Assign.objects.get(id=assignment_id)
        assignment.delete()
        messages.success(request, _(
            'Teaching assignment has been deleted successfully!'))
    except Assign.DoesNotExist:
        messages.error(request, _('The teaching assignment does not exist!'))

    return redirect('teaching_assignments')

@login_required
def timetable(request):
    """
    View for managing timetable
    """
    filter_form = TimetableFilterForm(request.GET)
    timetable_entries = AssignTime.objects.select_related(
        'assign__subject', 'assign__teacher', 'assign__class_id'
    )

    if filter_form.is_valid():
        class_id = filter_form.cleaned_data.get('class_id')
        teacher = filter_form.cleaned_data.get('teacher')
        day = filter_form.cleaned_data.get('day')

        if class_id:
            timetable_entries = timetable_entries.filter(
                assign__class_id=class_id)
        if teacher:
            timetable_entries = timetable_entries.filter(
                assign__teacher=teacher)
        if day:
            timetable_entries = timetable_entries.filter(day=day)

    context = {
        'timetable_entries': timetable_entries,
        'filter_form': filter_form,
        'admin_user': request.user,
    }
    return render(request, 'admins/timetable.html', context)


@login_required
@permission_required('assign.add_assigntime', raise_exception=True)
def add_timetable_entry(request):
    """
    View for adding new timetable entry
    """
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _(
                'Timetable entry has been added successfully!'))
            return redirect('timetable')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, _(error))
    else:
        form = TimetableForm()

    context = {
        'form': form,
        'admin_user': request.user,
        'title': _('Add Timetable Entry')
    }
    return render(request, 'admins/timetable_form.html', context)


@login_required
@permission_required('assign.change_assigntime', raise_exception=True)
def edit_timetable_entry(request, entry_id):
    """
    View for editing timetable entry
    """
    try:
        entry = AssignTime.objects.get(id=entry_id)
    except AssignTime.DoesNotExist:
        messages.error(request, _('The timetable entry does not exist!'))
        return redirect('timetable')

    if request.method == 'POST':
        form = TimetableForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, _(
                'Timetable entry has been updated successfully!'))
            return redirect('timetable')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, _(error))
    else:
        form = TimetableForm(instance=entry)

    context = {
        'form': form,
        'entry': entry,
        'admin_user': request.user,
        'title': _('Edit Timetable Entry')
    }
    return render(request, 'admins/timetable_form.html', context)


@login_required
@permission_required('assign.delete_assigntime', raise_exception=True)
def delete_timetable_entry(request, entry_id):
    """
    View for deleting timetable entry
    """
    try:
        entry = AssignTime.objects.get(id=entry_id)
        entry.delete()
        messages.success(request, _(
            'Timetable entry has been deleted successfully!'))
    except AssignTime.DoesNotExist:
        messages.error(request, _('The timetable entry does not exist!'))

    return redirect('timetable')

@login_required
def class_list(request):
    """
    View for listing all classes with pagination and filtering
    """
    # Handle filter form (optional, you can add a filter form later if needed)
    classes = Class.objects.all().order_by('id')

    # Pagination
    paginator = Paginator(classes, PAGE_SIZE)  # Use PAGE_SIZE from constants
    page_number = request.GET.get('page')
    classes_page = paginator.get_page(page_number)

    context = {
        'classes': classes_page,
        'admin_user': request.user,
        'title': _('Manage Classes'),
    }
    return render(request, 'admins/class_list.html', context)


@login_required
@permission_required('admins.add_class', raise_exception=True)
def add_class(request):
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _(
                    'Class has been added successfully!'))
                return redirect('class_list')
            except Exception as e:
                messages.error(request, _(
                    'Error creating class: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = ClassForm()

    context = {
        'form': form,
        'admin_user': request.user,
        'title': _('Add Class'),
        'submit_text': _('Add Class'),
        'students': [],  # Không có học sinh khi thêm mới lớp
    }
    return render(request, 'admins/class_form.html', context)


@login_required
@permission_required('admins.change_class', raise_exception=True)
def edit_class(request, class_id):
    try:
        class_obj = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        messages.error(request, _('The class does not exist!'))
        return redirect('class_list')

    # Lấy danh sách học sinh và các Assign records (môn học) thuộc lớp
    students = Student.objects.filter(class_id=class_obj).order_by('name')
    assignments = Assign.objects.filter(class_id=class_obj).select_related('subject', 'teacher').order_by('subject__id')

    # Phân trang cho học sinh
    paginator = Paginator(students, PAGE_SIZE)
    page_number = request.GET.get('page')
    students_page = paginator.get_page(page_number)

    # Phân trang cho môn học (assignments)
    assignments_paginator = Paginator(assignments, PAGE_SIZE)
    assignments_page_number = request.GET.get('assignments_page')
    assignments_page = assignments_paginator.get_page(assignments_page_number)

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_obj)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _(
                    'Class has been updated successfully!'))
                return redirect('class_list')
            except Exception as e:
                messages.error(request, _(
                    'Error updating class: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = ClassForm(instance=class_obj)

    context = {
        'form': form,
        'class_obj': class_obj,
        'admin_user': request.user,
        'title': _('Edit Class'),
        'submit_text': _('Update Class'),
        'students': students_page,
        'assignments': assignments_page,
    }
    return render(request, 'admins/class_form.html', context)

@login_required
@permission_required('admins.delete_class', raise_exception=True)
def delete_class(request, class_id):
    """
    View để xóa lớp (chỉ xóa nếu không có học sinh nào )
    """
    try:
        class_obj = Class.objects.get(id=class_id)
        students_count = class_obj.student_set.count()

        if students_count > ZERO:
            messages.warning(request, _(
                'Cannot delete this class because it has %(count)d student(s).') % {'count': students_count})
        else:
            class_obj.delete()
            messages.success(request, _('Class has been deleted successfully!'))

    except Class.DoesNotExist:
        messages.error(request, _('The class does not exist!'))

    return redirect('class_list')


@login_required
@permission_required('students.add_student', raise_exception=True)
def add_student_to_class(request, class_id):
    """
    View để thêm học sinh vào lớp
    """
    try:
        class_obj = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        messages.error(request, _('The class does not exist!'))
        return redirect('class_list')

    if request.method == 'POST':
        form = AddStudentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Tạo tài khoản người dùng
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['name'].split()[0],
                        last_name=' '.join(form.cleaned_data['name'].split()[1:]) if len(
                            form.cleaned_data['name'].split()) > 1 else ''
                    )

                    # Tạo hồ sơ học sinh
                    student = Student.objects.create(
                        user=user,
                        USN=form.cleaned_data['USN'],
                        name=form.cleaned_data['name'],
                        sex=form.cleaned_data['sex'],
                        DOB=form.cleaned_data['DOB'],
                        address=form.cleaned_data['address'],
                        phone=form.cleaned_data['phone'],
                        class_id=class_obj  # Gán lớp cụ thể
                    )

                    messages.success(request, _(
                        'Student "{}" has been successfully added to class.').format(student.name))
                    return redirect('edit_class', class_id=class_id)
            except Exception as e:
                messages.error(request, _(
                    'Error creating student: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = AddStudentForm(initial={'class_id': class_obj})

    context = {
        'form': form,
        'class_obj': class_obj,
        'admin_user': request.user,
        'title': _('Add Student to {}').format(class_obj),
        'submit_text': _('Add Student'),
    }
    return render(request, 'admins/add_student_to_class.html', context)


@login_required
@permission_required('students.change_student', raise_exception=True)
def edit_student(request, student_id):
    """
    View để sửa thông tin học sinh sử dụng EditStudentForm riêng
    """
    try:
        student = Student.objects.get(USN=student_id)
    except Student.DoesNotExist:
        messages.error(request, _('The student does not exist!'))
        return redirect('class_list')

    if request.method == 'POST':
        # Sử dụng EditStudentForm thay vì AddStudentForm
        form = EditStudentForm(request.POST, instance=student)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Cập nhật User model
                    user = student.user

                    # Cập nhật username nếu khác
                    new_username = form.cleaned_data.get('username')
                    if new_username and new_username != user.username:
                        user.username = new_username

                    # Cập nhật email nếu khác
                    new_email = form.cleaned_data.get('email')
                    if new_email and new_email != user.email:
                        user.email = new_email

                    # Cập nhật password nếu được cung cấp
                    new_password = form.cleaned_data.get('password')
                    if new_password and new_password.strip():
                        user.set_password(new_password)

                    # Cập nhật first_name và last_name từ name
                    new_name = form.cleaned_data.get('name')
                    if new_name:
                        name_parts = new_name.split()
                        user.first_name = name_parts[0] if name_parts else ''
                        user.last_name = ' '.join(name_parts[1:]) if len(
                            name_parts) > 1 else ''

                    user.save()

                    # Cập nhật Student model (form.save() sẽ tự động update vì có instance)
                    form.save()

                    messages.success(request, _(
                        'Student "{}" has been updated successfully!').format(student.name))
                    return redirect('edit_class', class_id=student.class_id.id)

            except Exception as e:
                messages.error(request, _(
                    'Error updating student: {}').format(str(e)))
        else:
            # Hiển thị lỗi validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # GET request - hiển thị form với dữ liệu hiện tại
        form = EditStudentForm(instance=student)

    context = {
        'form': form,
        'student': student,
        'admin_user': request.user,
        'title': _('Edit Student {}').format(student.name),
        'submit_text': _('Update Student'),
    }
    return render(request, 'admins/edit_student.html', context)

@login_required
@permission_required('students.delete_student', raise_exception=True)
def delete_student(request, student_id):
    """
    View để xóa học sinh.
    - Nếu học sinh đã tham gia học (có StudentSubject, Attendance, hoặc Marks): Deactivate
    - Nếu chưa có dữ liệu liên quan: Xóa hoàn toàn
    """
    try:
        student = Student.objects.get(USN=student_id)
        class_id = student.class_id.id

        # Kiểm tra xem có dữ liệu học tập liên quan không
        has_student_subjects = StudentSubject.objects.filter(student=student).exists()
        has_attendance = Attendance.objects.filter(student=student).exists()
        has_attendance_total = AttendanceTotal.objects.filter(student=student).exists()
        has_marks = Marks.objects.filter(student_subject__student=student).exists()

        has_related_data = any([
            has_student_subjects,
            has_attendance,
            has_attendance_total,
            has_marks
        ])

        if has_related_data:
            # Chỉ deactivate student
            student.user.is_active = False
            student.user.save()
            student.is_active = False 
            student.save()
            messages.warning(request, _(
                'Student has academic records and has been deactivated instead of deleted.'))
        else:
            # Nếu chưa tham gia học thì cho phép xóa hoàn toàn
            student.user.delete()
            student.delete()
            messages.success(request, _('Student has been deleted successfully!'))

    except Student.DoesNotExist:
        messages.error(request, _('The student does not exist!'))

    return redirect('edit_class', class_id=class_id)

@login_required
def department_list(request):
    """
    View for listing all departments with pagination
    """
    departments = Dept.objects.all().order_by('id')
    
    # Pagination
    paginator = Paginator(departments, PAGE_SIZE)
    page_number = request.GET.get('page')
    departments_page = paginator.get_page(page_number)
    
    context = {
        'departments': departments_page,
        'admin_user': request.user,
        'title': _('Manage Departments'),
    }
    return render(request, 'admins/department_list.html', context)

@login_required
@permission_required('admins.add_dept', raise_exception=True)
def add_department(request):
    """
    View để thêm department mới
    """
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('Department has been added successfully!'))
                return redirect('department_list')
            except Exception as e:
                messages.error(request, _('Error creating department: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'admin_user': request.user,
        'title': _('Add Department'),
        'submit_text': _('Add Department'),
    }
    return render(request, 'admins/department_form.html', context)

@login_required
@permission_required('admins.change_dept', raise_exception=True)
def edit_department(request, dept_id):
    """
    View để sửa department 
    """
    try:
        department = Dept.objects.get(id=dept_id)
    except Dept.DoesNotExist:
        messages.error(request, _('The department does not exist!'))
        return redirect('department_list')
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('Department has been updated successfully!'))
                return redirect('department_list')
            except Exception as e:
                messages.error(request, _('Error updating department: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
        'admin_user': request.user,
        'title': _('Edit Department'),
        'submit_text': _('Update Department'),
    }
    return render(request, 'admins/department_form.html', context)

@login_required
@permission_required('admins.delete_dept', raise_exception=True)
def delete_department(request, dept_id):
    """
    View để xóa khoa:
    - Nếu đã có Teacher, Subject, hoặc Class thuộc khoa này → không cho xóa.
    - Nếu không có dữ liệu liên quan → xóa hoàn toàn.
    """
    try:
        department = Dept.objects.get(id=dept_id)

        # Kiểm tra dữ liệu liên quan
        has_teachers = Teacher.objects.filter(dept=department).exists()
        has_subjects = Subject.objects.filter(dept=department).exists()
        has_classes = Class.objects.filter(dept=department).exists()

        if any([has_teachers, has_subjects, has_classes]):
            messages.warning(request, _(
                'Cannot delete department because it has related teachers, subjects, or classes.'))
        else:
            department.delete()
            messages.success(request, _('Department has been deleted successfully!'))

    except Dept.DoesNotExist:
        messages.error(request, _('The department does not exist!'))

    return redirect('department_list')

@login_required
@permission_required('admins.add_subject', raise_exception=True)
def add_subject(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('Subject has been added successfully!'))
                return redirect('subject_list')
            except Exception as e:
                messages.error(request, _('Error creating subject: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SubjectForm()

    context = {
        'form': form,
        'admin_user': request.user,
        'title': _('Add Subject'),
        'submit_text': _('Add Subject'),
    }
    return render(request, 'admins/subject_form.html', context)

@login_required
@permission_required('admins.change_subject', raise_exception=True)
def edit_subject(request, subject_id):
    try:
        subject = Subject.objects.get(id=subject_id)
    except Subject.DoesNotExist:
        messages.error(request, _('The subject does not exist!'))
        return redirect('subject_list')

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _('Subject has been updated successfully!'))
                return redirect('subject_list')
            except Exception as e:
                messages.error(request, _('Error updating subject: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SubjectForm(instance=subject)

    context = {
        'form': form,
        'subject': subject,
        'admin_user': request.user,
        'title': _('Edit Subject'),
        'submit_text': _('Update Subject'),
    }
    return render(request, 'admins/subject_form.html', context)

@login_required
def subject_list(request):
    subjects = Subject.objects.all().order_by('id')
    paginator = Paginator(subjects, PAGE_SIZE)
    page_number = request.GET.get('page')
    subjects_page = paginator.get_page(page_number)

    context = {
        'subjects': subjects_page,
        'admin_user': request.user,
        'title': _('Manage Subjects'),
    }
    return render(request, 'admins/subject_list.html', context)

@login_required
@permission_required('admins.delete_subject', raise_exception=True)
def delete_subject(request, subject_id):
    try:
        subject = Subject.objects.get(id=subject_id)
        # Kiểm tra data
        has_assignments = Assign.objects.filter(subject=subject).exists()
        has_student_subjects = StudentSubject.objects.filter(subject=subject).exists()
        if has_assignments or has_student_subjects:
            messages.warning(request, _('Cannot delete subject because it has related assignments or student records.'))
        else:
            subject.delete()
            messages.success(request, _('Subject has been deleted successfully!'))
    except Subject.DoesNotExist:
        messages.error(request, _('The subject does not exist!'))
    return redirect('subject_list')

@login_required
@permission_required('assign.add_assign', raise_exception=True)
def add_subject_to_class(request, class_id):
    """
    View để thêm subject vào class 
    """
    try:
        class_obj = Class.objects.get(id=class_id)
    except Class.DoesNotExist:
        messages.error(request, _('The class does not exist!'))
        return redirect('class_list')

    if request.method == 'POST':
        form = AddSubjectToClassForm(request.POST, class_obj=class_obj)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create a new Assign record
                    Assign.objects.create(
                        class_id=class_obj,
                        subject=form.cleaned_data['subject'],
                        teacher=form.cleaned_data['teacher']
                    )
                    messages.success(request, _(
                        'Subject "{}" has been successfully assigned to class "{}".').format(
                            form.cleaned_data['subject'], class_obj))
                    return redirect('edit_class', class_id=class_id)
            except Exception as e:
                messages.error(request, _(
                    'Error assigning subject to class: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = AddSubjectToClassForm(class_obj=class_obj)

    context = {
        'form': form,
        'class_obj': class_obj,
        'admin_user': request.user,
        'title': _('Add Subject to {}').format(class_obj),
        'submit_text': _('Add Subject'),
    }
    return render(request, 'admins/add_subject_to_class.html', context)

@login_required
@permission_required('assign.delete_assign', raise_exception=True)
def remove_subject_from_class(request, class_id, assign_id):
    """
    View để xóa subject khỏi class 
    """
    try:
        class_obj = Class.objects.get(id=class_id)
        assign = Assign.objects.get(id=assign_id, class_id=class_obj)
        subject_name = assign.subject.name
        assign.delete()
        messages.success(request, _(
            'Subject "{}" has been removed from class "{}".').format(subject_name, class_obj))
    except Class.DoesNotExist:
        messages.error(request, _('The class does not exist!'))
    except Assign.DoesNotExist:
        messages.error(request, _('The assignment does not exist!'))
    return redirect('edit_class', class_id=class_id)

def _get_performance_report_context(total_students: int):
    """Build context for Student Performance report."""
    student_performance = StudentSubject.objects.select_related('student', 'subject').annotate(
        avg_marks=Avg('marks__marks1')
    ).filter(marks__isnull=False)

    top_students = student_performance.order_by('-avg_marks')[:10]

    class_performance = Class.objects.annotate(
        student_count=Count('student'),
        avg_performance=Avg('student__studentsubject__marks__marks1')
    )

    return {
        'report_type': 'performance',
        'total_students': total_students,
        'top_students': top_students,
        'class_performance': class_performance,
        'title': 'Student Performance Report'
    }


def _get_attendance_report_context():
    """Build context for Attendance report."""
    today = timezone.now().date()
    month_ago = today - timedelta(days=30)

    student_attendance = Attendance.objects.filter(
        date__gte=month_ago
    ).values(
        'student__class_id__id',
        'student__class_id__section',
        'student__class_id__sem',
        'student__class_id__dept__name',
    ).annotate(
        total_records=Count('id'),
        present_records=Count('id', filter=Q(status=True)),
        absent_records=Count('id', filter=Q(status=False))
    ).order_by('student__class_id__id')

    teacher_attendance = AttendanceClass.objects.filter(
        date__gte=month_ago
    ).values('assign__teacher__name').annotate(
        total_classes=Count('date'),
        present_classes=Count('date', filter=Q(status=True)),
        absent_classes=Count('date', filter=Q(status=False))
    ).order_by('assign__teacher__name')

    return {
        'report_type': 'attendance',
        'student_attendance': student_attendance,
        'teacher_attendance': teacher_attendance,
        'title': 'Attendance Report'
    }


def _get_teaching_report_context():
    """Build context for Teaching Analytics report."""
    teaching_assignments = Assign.objects.select_related('teacher', 'subject', 'class_id').annotate(
        total_students=Count('class_id__student')
    )

    teacher_workload = Teacher.objects.annotate(
        total_assignments=Count('assign'),
        total_classes=Count('assign__class_id', distinct=True),
        total_students=Count('assign__class_id__student')
    )

    subject_distribution = Subject.objects.annotate(
        assignment_count=Count('assign'),
        teacher_count=Count('assign__teacher', distinct=True),
        class_count=Count('assign__class_id', distinct=True)
    )

    return {
        'report_type': 'teaching',
        'teaching_assignments': teaching_assignments,
        'teacher_workload': teacher_workload,
        'subject_distribution': subject_distribution,
        'title': 'Teaching Analytics Report'
    }


def _get_data_report_context():
    """Build context for Data Management report."""
    department_stats = Dept.objects.annotate(
        class_count=Count('class', distinct=True),
        student_count=Count('class__student', distinct=True),
        teacher_count=Count('class__assign__teacher', distinct=True)
    )

    class_stats = Class.objects.annotate(
        student_count=Count('student', distinct=True),
        subject_count=Count('assign__subject', distinct=True),
        teacher_count=Count('assign__teacher', distinct=True)
    )

    subject_stats = Subject.objects.annotate(
        assignment_count=Count('assign', distinct=True),
        class_count=Count('assign__class_id', distinct=True),
        student_count=Count('assign__class_id__student', distinct=True)
    )

    return {
        'report_type': 'data',
        'department_stats': department_stats,
        'class_stats': class_stats,
        'subject_stats': subject_stats,
        'title': 'Data Management Report'
    }


def _get_export_report_context():
    """Build context for Export report."""
    return {
        'report_type': 'export',
        'title': 'Export Data'
    }


def _get_overview_report_context(total_students: int, total_teachers: int, total_classes: int,
                                 total_departments: int, total_subjects: int):
    """Build context for Overview report."""
    recent_students = Student.objects.order_by('-USN')[:5]
    recent_teachers = Teacher.objects.order_by('-id')[:5]
    recent_classes = Class.objects.order_by('-id')[:5]

    system_stats = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_departments': total_departments,
        'total_subjects': total_subjects,
        'total_assignments': Assign.objects.count(),
        'total_exam_sessions': ExamSession.objects.count(),
        'total_attendance_records': Attendance.objects.count()
    }

    return {
        'report_type': 'overview',
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
        'recent_classes': recent_classes,
        'system_stats': system_stats,
        'title': 'Reports & Statistics Overview'
    }


@login_required
def admin_reports(request):
    """Admin Reports and Statistics Dashboard"""
    report_type = request.GET.get('type', 'overview')

    # Common totals used across views and summary
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_classes = Class.objects.count()
    total_departments = Dept.objects.count()
    total_subjects = Subject.objects.count()

    # Dispatch to the appropriate report builder
    if report_type == 'performance':
        context = _get_performance_report_context(total_students)
    elif report_type == 'attendance':
        context = _get_attendance_report_context()
    elif report_type == 'teaching':
        context = _get_teaching_report_context()
    elif report_type == 'data':
        context = _get_data_report_context()
    elif report_type == 'export':
        context = _get_export_report_context()
    else:
        context = _get_overview_report_context(
            total_students, total_teachers, total_classes, total_departments, total_subjects
        )

    # Add common context
    context.update({
        'admin_user': request.user,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_departments': total_departments,
        'total_subjects': total_subjects,
        'current_date': timezone.now().date(),
        'report_types': [
            ('overview', 'Overview'),
            ('performance', 'Student Performance'),
            ('attendance', 'Attendance Reports'),
            ('teaching', 'Teaching Analytics'),
            ('data', 'Data Management'),
            ('export', 'Export & Download')
        ]
    })

    return render(request, 'admins/admin_reports.html', context)

@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list(request):
    """
    View list, search, sort accounts
    """
    users = User.objects.all()

    # Handle search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        users = users.filter(
            username__icontains=search_query
        ) | users.filter(
            email__icontains=search_query
        )

    # Handle filter by is_active
    is_active_filter = request.GET.get('is_active')
    if is_active_filter == 'True':
        users = users.filter(is_active=True)
    elif is_active_filter == 'False':
        users = users.filter(is_active=False)

    # Handle filter by role
    role_filter = request.GET.get('role')
    if role_filter == 'admin':
        users = users.filter(is_superuser=True)
    elif role_filter == 'student':
        users = users.filter(student__isnull=False)
    elif role_filter == 'teacher':
        users = users.filter(teacher__isnull=False)
    elif role_filter == 'user':
        users = users.filter(is_superuser=False,
                             student__isnull=True, teacher__isnull=True)

    # Handle sorting
    sort = request.GET.get('sort')
    direction = request.GET.get('dir', 'asc')
    if sort:
        if sort == 'username':
            users = users.order_by(
                'username' if direction == 'asc' else '-username')
        elif sort == 'full_name':
            users = users.order_by(
                'first_name' if direction == 'asc' else '-first_name')
        elif sort == 'email':
            users = users.order_by('email' if direction == 'asc' else '-email')
        elif sort == 'role':
            # Sort logic
            users = users.annotate(
                role_order=Case(
                    When(is_superuser=True, then=Value(1)),
                    When(teacher__isnull=False, then=Value(2)),
                    When(student__isnull=False, then=Value(3)),
                    default=Value(4),
                    output_field=IntegerField()
                )
            ).order_by('role_order' if direction == 'asc' else '-role_order')

    # Pagination
    paginator = Paginator(users, PAGE_SIZE)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)

    context = {
        'users': users_page,
        'admin_user': request.user,
        'title': _('Manage Users'),
    }
    return render(request, 'admins/user_list.html', context)


@login_required
@permission_required('auth.add_user', raise_exception=True)
def add_user(request):
    """
    View add user mới
    """
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        is_superuser=form.cleaned_data['is_superuser'],
                        is_active=form.cleaned_data['is_active']
                    )
                    messages.success(request, _(
                        'User "{}" has been added successfully!').format(user.username))
                    return redirect('user_list')
            except Exception as e:
                messages.error(request, _(
                    'Error creating user: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = AddUserForm()

    context = {
        'form': form,
        'admin_user': request.user,
        'title': _('Add User'),
        'submit_text': _('Add User'),
    }
    return render(request, 'admins/user_form.html', context)


@login_required
@permission_required('auth.change_user', raise_exception=True)
def edit_user(request, user_id):
    """
    View edit account
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, _('The user does not exist!'))
        return redirect('user_list')

    if request.method == 'POST':
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    if form.cleaned_data['password']:
                        user.set_password(form.cleaned_data['password'])
                    user.save()
                    messages.success(request, _(
                        'User "{}" has been updated successfully!').format(user.username))
                    return redirect('user_list')
            except Exception as e:
                messages.error(request, _(
                    'Error updating user: {}').format(str(e)))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = EditUserForm(instance=user)

    context = {
        'form': form,
        'user_obj': user,
        'admin_user': request.user,
        'title': _('Edit User {}').format(user.username),
        'submit_text': _('Update User'),
    }
    return render(request, 'admins/user_form.html', context)


@login_required
@permission_required('auth.delete_user', raise_exception=True)
def toggle_user_status(request, user_id):
    """
    View khóa, mở khóa tk
    """
    try:
        user = User.objects.get(id=user_id)
        if user == request.user:
            messages.error(request, _(
                'You cannot deactivate your own account!'))
        else:
            user.is_active = not user.is_active
            user.save()
            status = 'activated' if user.is_active else 'deactivated'
            messages.success(request, _(
                'User "{}" has been {} successfully!').format(user.username, status))
    except User.DoesNotExist:
        messages.error(request, _('The user does not exist!'))
    return redirect('user_list')

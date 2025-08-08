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
    AddSubjectToClassForm)
# Model imports
from students.models import Student, Attendance, StudentSubject, AttendanceTotal
from teachers.models import Teacher, Assign, AssignTime, Marks
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


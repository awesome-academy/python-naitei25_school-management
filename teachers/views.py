from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from teachers.models import Teacher
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import Teacher, Assign, ExamSession, Marks, AssignTime, AttendanceClass
from students.models import Attendance, StudentSubject
from django.db import transaction
from utils.date_utils import determine_semester, determine_academic_year_start
from datetime import datetime, timedelta, date
import math

from utils.constant import (
    DAYS_OF_WEEK, TIME_SLOTS, TIMETABLE_TIME_SLOTS,
    TIMETABLE_DAYS_COUNT, TIMETABLE_PERIODS_COUNT, TIMETABLE_DEFAULT_VALUE,
    TIMETABLE_SKIP_PERIODS, TIMETABLE_ACCESS_DENIED_MESSAGE,
    FREE_TEACHERS_NO_AVAILABLE_TEACHERS_MESSAGE, FREE_TEACHERS_NO_SUBJECT_KNOWLEDGE_MESSAGE,
    TEACHER_FILTER_DISTINCT_ENABLED, TEACHER_FILTER_BY_CLASS, TEACHER_FILTER_BY_SUBJECT_KNOWLEDGE, DATE_FORMAT,
    ATTENDANCE_STANDARD, CIE_STANDARD,TEST_NAME_CHOICES, BREAK_PERIOD, LUNCH_PERIOD,
    CIE_CALCULATION_LIMIT, CIE_DIVISOR
)


def _calculate_attendance_statistics(attendance_queryset):
    """
    Private function to calculate attendance statistics from an attendance queryset.
    
    Args:
        attendance_queryset: QuerySet of Attendance objects
        
    Returns:
        dict: Dictionary containing attendance statistics with keys:
            - total_students: Total number of students
            - present_students: Number of present students
            - absent_students: Number of absent students  
            - attendance_percentage: Attendance percentage (rounded to 1 decimal)
    """
    total_students = attendance_queryset.count()
    present_students = attendance_queryset.filter(status=True).count()
    absent_students = total_students - present_students
    attendance_percentage = round(
        (present_students / total_students * 100), 1
    ) if total_students > 0 else 0
    
    return {
        'total_students': total_students,
        'present_students': present_students,
        'absent_students': absent_students,
        'attendance_percentage': attendance_percentage,
    }


@login_required
def teacher_dashboard(request):
    """
    Teacher dashboard view - only accessible to authenticated teachers
    """
    # Check if user is a teacher
    if not getattr(request.user, 'is_teacher', False):
        messages.error(request, _(
            'Access denied. Teacher credentials required.'))
        return redirect('unified_login')

    # Get teacher profile
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, _(
            'Teacher profile not found. Please contact administrator.'))
        return redirect('unified_logout')

    context = {
        'teacher': teacher,
        'user': request.user,
    }

    return render(request, 't_homepage.html', context)


def teacher_logout(request):
    """
    Teacher logout view - redirects to unified logout
    """
    return redirect('unified_logout')


# Legacy view for backward compatibility
@login_required
def index(request):
    """
    Legacy teacher index view - redirects to new dashboard
    """
    return redirect('teacher_dashboard')

# Teacher Views
# Hiển thị thông tin lớp học hoặc các lựa chọn liên quan đến giáo viên.


@login_required
def t_clas(request, teacher_id, choice):
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    teacher1 = get_object_or_404(Teacher, id=teacher_id)

    # Lấy tất cả assignments của giáo viên (bao gồm cả các kỳ khác nhau)
    assignments = Assign.objects.filter(
        teacher=teacher1
    ).select_related('class_id', 'subject', 'class_id__dept')
    
    # Debug removed
    
    # Lấy các tham số lọc từ request
    selected_year = request.GET.get('academic_year', '')
    selected_semester = request.GET.get('semester', '')
    
    # Debug removed
    
    # Áp dụng bộ lọc
    if selected_year and selected_semester and selected_semester.isdigit():
        # Lọc theo cả năm và kỳ cùng lúc để tránh nhầm lẫn
        semester_int = int(selected_semester)
        
        # Tìm các assignments có year_sem khớp với yêu cầu
        # Sử dụng property year_sem để lọc chính xác
        target_year_sem = f"{selected_year}.{semester_int}"
        # Debug removed
        
        # Lọc bằng cách kiểm tra academic_year và semester
        # Chỉ lấy assignments mà year_sem property khớp với target
        filtered_assignments = []
        for ass in assignments:
            if ass.year_sem == target_year_sem:
                filtered_assignments.append(ass.id)
        
        assignments = assignments.filter(id__in=filtered_assignments)
        # Debug removed
        
    elif selected_year:
        # Nếu chỉ chọn năm, tìm tất cả academic_year chứa năm đó
        assignments = assignments.filter(academic_year__icontains=selected_year)
        # Debug removed
    
    elif selected_semester and selected_semester.isdigit():
        # Nếu chỉ chọn kỳ
        semester_int = int(selected_semester)
        assignments = assignments.filter(semester=semester_int)
        # Debug removed
    
    # Hiển thị kết quả cuối cùng
    # Debug removed
    
    # Sắp xếp assignments
    assignments = assignments.order_by('class_id__dept__name', 'class_id__sem', 'class_id__section', 'subject__name')
    
    # Pagination - 10 items per page
    paginator = Paginator(assignments, 10)
    page = request.GET.get('page')
    
    try:
        assignments = paginator.page(page)
    except PageNotAnInteger:
        assignments = paginator.page(1)
    except EmptyPage:
        assignments = paginator.page(paginator.num_pages)
    
    # Lấy danh sách các năm học và học kỳ để hiển thị trong bộ lọc (tất cả assignments)
    all_assignments_for_filter = Assign.objects.filter(teacher=teacher1)
    
    # Lấy tất cả academic_year và extract năm từ chúng
    academic_year_strings = (
        all_assignments_for_filter
        .values_list('academic_year', flat=True)
        .distinct()
    )
    
    # Extract các năm từ academic_year (ví dụ: "2024-2025" -> ["2024", "2025"])
    years_set = set()
    for year_str in academic_year_strings:
        import re
        # Tìm tất cả số 4 chữ số trong academic_year
        years_found = re.findall(r'\d{4}', str(year_str))
        years_set.update(years_found)
    
    # Sắp xếp các năm giảm dần
    academic_years = sorted(list(years_set), reverse=True)
    
    # Debug: Xem các năm học có sẵn
    # Debug removed
    
    # Lấy các học kỳ có sẵn
    available_semesters = sorted(list(
        all_assignments_for_filter
        .values_list('semester', flat=True)
        .distinct()
    ))
    # Debug removed
    
    # Sử dụng học kỳ thực tế từ database hoặc fallback to 1-3
    semesters = available_semesters if available_semesters else range(1, 4)
    
    # Convert selected_semester to int for template comparison
    selected_semester_int = int(selected_semester) if selected_semester and selected_semester.isdigit() else None
    # Get filter parameters
    selected_semester = request.GET.get('semester', '')
    selected_academic_year = request.GET.get('academic_year', '')
    
    # Start with all assignments for this teacher
    assignments = teacher1.assign_set.all()
    
    # Apply filters if provided
    if selected_semester:
        try:
            semester_int = int(selected_semester)
            assignments = assignments.filter(semester=semester_int)
        except ValueError:
            pass
    
    if selected_academic_year:
        # Filter assignments where the selected year matches the semester's year
        # For "2024-2025": semester 1,2,3 -> 2024.X, semester 1,2,3 of next year -> 2025.X
        from django.db.models import Q
        
        # Find assignments where the year should be displayed for the semester
        year_filter = Q()
        
        # For academic years like "2024-2025"
        # Semester 1: Sep-Jan -> belongs to first year (2024)
        # Semester 2: Feb-Jun -> belongs to second year (2025) 
        # Semester 3: Jul-Aug -> belongs to second year (2025)
        
        for assignment in teacher1.assign_set.all():
            academic_year_str = str(assignment.academic_year)
            import re
            years = re.findall(r'\b\d{4}\b', academic_year_str)
            
            if len(years) >= 2:  # Format like "2024-2025"
                first_year, second_year = years[0], years[1]
                
                # Determine which year this semester belongs to
                if assignment.semester == 1:
                    display_year = first_year
                else:  # semester 2 or 3
                    display_year = second_year
                    
                if display_year == selected_academic_year:
                    year_filter |= Q(id=assignment.id)
            else:  # Single year format like "2024"
                if selected_academic_year in academic_year_str:
                    year_filter |= Q(id=assignment.id)
        
        assignments = assignments.filter(year_filter)
    
    # Get available options for dropdowns
    all_assignments = teacher1.assign_set.all()
    available_semesters = sorted(set(all_assignments.values_list('semester', flat=True)))
    
    # Extract individual years from academic_year strings for dropdown
    # e.g., "2023-2024" -> [2023, 2024], "2024-2025" -> [2024, 2025]
    academic_years = all_assignments.values_list('academic_year', flat=True)
    individual_years = set()
    for year_str in academic_years:
        # Use regex to find all 4-digit years in the string
        import re
        years_found = re.findall(r'\b\d{4}\b', str(year_str))
        for year in years_found:
            individual_years.add(year)
    
    available_years = sorted(individual_years)
    
    context = {
        'teacher1': teacher1,
        'choice': choice,
        'assignments': assignments,
        'academic_years': academic_years,
        'semesters': semesters,
        'available_semesters': available_semesters,
        'selected_year': selected_year,
        'selected_semester': selected_semester,
        'selected_semester_int': selected_semester_int,
    }
        'available_semesters': available_semesters,
        'available_years': available_years,
        'selected_semester': selected_semester,
        'selected_academic_year': selected_academic_year,
    }
    
    return render(request, 't_clas.html', context)

# Hiển thị danh sách các phiên thi (ExamSession) của một assignment (môn học/lớp/giáo viên).


@login_required
def t_marks_list(request, assign_id):
    assignment = get_object_or_404(Assign, id=assign_id)
    
    # Kiểm tra xem user hiện tại có phải là giáo viên của assignment này không
    if hasattr(assignment.teacher, 'user') and assignment.teacher.user and assignment.teacher.user != request.user:
        messages.error(request, _('Bạn không có quyền truy cập assignment này!'))
        return redirect('teacher_dashboard')
    
    # Lấy exam sessions của assignment này
    exam_sessions_list = ExamSession.objects.filter(assign=assignment)
    
    # Xử lý tạo bài kiểm tra mới
    if request.method == 'POST' and 'create_exam' in request.POST:
        from utils.constant import TEST_NAME_CHOICES
        exam_name = request.POST.get('exam_name')
        if exam_name:
            try:
                new_exam, created = ExamSession.objects.get_or_create(
                    assign=assignment,
                    name=exam_name,
                    defaults={'status': False}
                )
                if created:
                    messages.success(request, _('Bài kiểm tra "%(exam_name)s" đã được tạo thành công!') % {'exam_name': exam_name})
                else:
                    messages.warning(request, _('Bài kiểm tra "%(exam_name)s" đã tồn tại!') % {'exam_name': exam_name})
            except Exception as e:
                messages.error(request, _('Lỗi khi tạo bài kiểm tra: %(error)s') % {'error': str(e)})
        else:
            messages.error(request, _('Vui lòng nhập tên bài kiểm tra!'))
    
        return redirect('t_marks_list', assign_id=assign_id)
    
    from utils.constant import TEST_NAME_CHOICES
    
    # Thống kê bài kiểm tra
    total_exams = exam_sessions_list.count()
    completed_exams = exam_sessions_list.filter(status=True).count()
    pending_exams = total_exams - completed_exams
    
    context = {
        'assignment': assignment,
        'm_list': exam_sessions_list,
        'exam_names': TEST_NAME_CHOICES,
        'total_exams': total_exams,
        'completed_exams': completed_exams,
        'pending_exams': pending_exams,
    }
    return render(request, 't_marks_list.html', context)

# Hiển thị form nhập điểm cho các học sinh đang học môn học này trong lớp.
# Chỉ hiển thị học sinh đã đăng ký môn học (StudentSubject).


@login_required()
def t_marks_entry(request, marks_c_id):
    with transaction.atomic():
        exam_session = get_object_or_404(ExamSession, id=marks_c_id)
        assignment = exam_session.assign
        subject = assignment.subject
        class_obj = assignment.class_id

        # Debug removed
        
        # Lấy tất cả học sinh trong lớp này
        all_students_in_class = class_obj.student_set.all().order_by('name')
        
        # Pagination for student list
        from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
        students_total = all_students_in_class.count()
        paginator = Paginator(all_students_in_class, 20)  # 20 students per page
        page = request.GET.get('page')
        try:
            students_page = paginator.page(page)
        except PageNotAnInteger:
            students_page = paginator.page(1)
        except EmptyPage:
            students_page = paginator.page(paginator.num_pages)

        # Prefill current marks for each student (if any)
        for student in students_page:
            # Kiểm tra xem học sinh có đăng ký môn học này không
            try:
                student_subject = StudentSubject.objects.get(
                    student=student,
                    subject=subject
                )
                latest_mark = (
                    student_subject.marks_set
                    .filter(name=exam_session.name)
                    .order_by('-id')
                    .first()
                )
                student.current_mark = latest_mark.marks1 if latest_mark else 0
                student.is_registered = True
            except StudentSubject.DoesNotExist:
                student.current_mark = 0
                student.is_registered = False

        context = {
            'ass': assignment,
            'c': class_obj,
            'mc': exam_session,
            'students_total': students_total,
            'students_page': students_page,
            'dept1': class_obj.dept,  # Thêm dept1 cho template
            'is_edit_mode': False,
        }
        return render(request, 't_marks_entry.html', context)

# Xử lý dữ liệu điểm số được nhập từ form.
# Lưu điểm cho từng học sinh vào database.
# Đánh dấu trạng thái phiên thi là đã hoàn thành.


@login_required()
def marks_confirm(request, marks_c_id):
    with transaction.atomic():
        exam_session = get_object_or_404(ExamSession, id=marks_c_id)
        assignment = exam_session.assign
        subject = assignment.subject
        class_object = assignment.class_id

        # Chỉ xử lý điểm cho những học sinh đã đăng ký môn học
        for student in class_object.student_set.all():
            student_mark = request.POST.get(student.USN)
            if student_mark is not None:  # Chỉ xử lý nếu có điểm được gửi
                try:
                    student_subject = StudentSubject.objects.get(
                        subject=subject, student=student)
                    marks_instance, _ = student_subject.marks_set.get_or_create(
                        name=exam_session.name)
                    marks_instance.marks1 = student_mark
                    marks_instance.save()
                except StudentSubject.DoesNotExist:
                    # Bỏ qua học sinh chưa đăng ký môn học
                    continue
        exam_session.status = True
        exam_session.save()

    return HttpResponseRedirect(reverse('t_marks_list', args=(assignment.id,)))

# Hiển thị form để chỉnh sửa điểm của các học sinh đang học môn học này trong lớp.
# Chỉ hiển thị học sinh đã đăng ký môn học (StudentSubject).
# Cho phép giáo viên cập nhật lại điểm số đã nhập.


@login_required()
def edit_marks(request, marks_c_id):
    with transaction.atomic():
        exam_session = get_object_or_404(ExamSession, id=marks_c_id)
        # Reuse t_marks_entry UI with prefilled marks
        assignment = exam_session.assign
        subject = assignment.subject
        class_object = assignment.class_id

        # Lấy tất cả học sinh trong lớp này
        all_students_in_class = class_object.student_set.all().order_by('name')

        # Pagination
        from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
        students_total = all_students_in_class.count()
        paginator = Paginator(all_students_in_class, 20)
        page = request.GET.get('page')
        try:
            students_page = paginator.page(page)
        except PageNotAnInteger:
            students_page = paginator.page(1)
        except EmptyPage:
            students_page = paginator.page(paginator.num_pages)

        # Prefill marks
        for student in students_page:
            # Kiểm tra xem học sinh có đăng ký môn học này không
            try:
                student_subject = StudentSubject.objects.get(
                    student=student,
                    subject=subject
                )
                latest_mark = (
                    student_subject.marks_set
                    .filter(name=exam_session.name)
                    .order_by('-id')
                    .first()
                )
                student.current_mark = latest_mark.marks1 if latest_mark else 0
                student.is_registered = True
            except StudentSubject.DoesNotExist:
                student.current_mark = 0
                student.is_registered = False

        context = {
            'ass': assignment,
            'c': class_object,
            'mc': exam_session,
            'students_total': students_total,
            'students_page': students_page,
            'dept1': class_object.dept,
            'is_edit_mode': True,
        }
        return render(request, 't_marks_entry.html', context)


@login_required()
def t_timetable(request, teacher_id):
    with transaction.atomic():
        teacher = get_object_or_404(Teacher, id=teacher_id)

        # Allow owner teacher OR staff/superuser to view
        if teacher.user != request.user and not (
            getattr(request.user, 'is_staff', False) or getattr(request.user, 'is_superuser', False)
        ):
            messages.error(request, _(TIMETABLE_ACCESS_DENIED_MESSAGE))
            return redirect('teacher_dashboard')

        asst = AssignTime.objects.filter(assign__teacher_id=teacher_id)

        # Filters
        year = request.GET.get('academic_year')
        sem = request.GET.get('semester')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        today = timezone.now().date()
        if not year:
            year = determine_academic_year_start(today)
        if not sem:
            sem = str(determine_semester(today))

        # Get date range from semester if not explicitly provided
        if not (start_date and end_date) and year and sem and sem.isdigit():
            from utils.date_utils import get_semester_date_range
            try:
                start, end = get_semester_date_range(year, int(sem))
                # Convert to string for template
                start_date = start.strftime("%Y-%m-%d")
                end_date = end.strftime("%Y-%m-%d")
            except (ValueError, IndexError):
                start = end = None
        else:
            # Parse explicit date range
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            except ValueError:
                start = end = None

        # Apply filters
        if year:
            asst = asst.filter(assign__academic_year__icontains=year)
        if sem and sem.isdigit():
            asst = asst.filter(assign__semester=int(sem))
            
        # Get week dates first
        week_start_str = request.GET.get('week_start')
        try:
            base_date = datetime.strptime(week_start_str, "%Y-%m-%d").date() if week_start_str else today
        except ValueError:
            base_date = today

        monday_start = base_date - timedelta(days=base_date.weekday())
        days = [day[0] for day in DAYS_OF_WEEK]  # Define days early
        day_to_date = {
            day_name: (monday_start + timedelta(days=idx)).strftime('%Y-%m-%d')
            for idx, day_name in enumerate(days)
        }
        prev_week_start = (monday_start - timedelta(days=7)).strftime('%Y-%m-%d')
        next_week_start = (monday_start + timedelta(days=7)).strftime('%Y-%m-%d')

        # Filter by date range if provided
        if start and end:
            # Convert day names to dates for the current week
            day_dates = {
                day: datetime.strptime(day_to_date[day], "%Y-%m-%d").date()
                for day in days
            }
            # Only keep assignments whose day falls within the date range
            asst = asst.filter(day__in=[
                day for day, date in day_dates.items()
                if start <= date <= end
            ])





        # Slots + Break/Lunch
        base_slots = [slot[0] for slot in TIME_SLOTS]
        time_slots = []
        for slot in base_slots:
            time_slots.append(slot)
            if slot == '9:30 - 10:30':
                time_slots.append(BREAK_PERIOD)
            elif slot == '12:40 - 1:30':
                time_slots.append(LUNCH_PERIOD)

        # Build timetable (match student structure exactly)
        timetable = {day: {slot: None for slot in time_slots} for day in days}
        for at in asst:
            if at.day in timetable and at.period in timetable[at.day]:
                timetable[at.day][at.period] = {
                    'subject': at.assign.subject,
                    'teacher': at.assign.teacher,
                    'assignment': at.assign
                }

        # Year options cho filter
        year_options = (
            AssignTime.objects
            .filter(assign__teacher_id=teacher_id)
            .values_list('assign__academic_year', flat=True)
            .distinct()
            .order_by('assign__academic_year')
        )

        context = {
            'teacher': teacher,  # Add teacher object
            'timetable': timetable,
            'days': days,
            'day_to_date': day_to_date,
            'time_slots': time_slots,  # Keep same name as template expects
            'week_start': monday_start.strftime('%Y-%m-%d'),
            'prev_week_start': prev_week_start,
            'next_week_start': next_week_start,

            'academic_year': year,
            'semester': sem,
            'year_options': list(year_options),
            'today': today.strftime('%Y-%m-%d'),
            'start_date': start_date if start_date else '',
            'end_date': end_date if end_date else '',
        }
        return render(request, 't_timetable.html', context)


@login_required()
def free_teachers(request, asst_id):
    with transaction.atomic():
        # Get the assignment time that needs replacement
        asst = get_object_or_404(AssignTime, id=asst_id)

        # Get the subject that needs to be taught
        required_subject = asst.assign.subject

        # Get unique teachers who teach in the same class (avoid duplicates)
        # Using distinct() because a teacher can have multiple assignments in the same class
        # Example: "phan thanh thắng" teaches 4 subjects in "SOICT : 2 a" class
        # Without distinct(), he would appear 4 times instead of 1
        t_list = Teacher.objects.filter(
            assign__class_id=asst.assign.class_id
        ).distinct()

        ft_list = []
        teachers_without_knowledge = []

        for t in t_list:
            # Get all teaching times for this teacher
            at_list = AssignTime.objects.filter(assign__teacher=t)

            # Check if teacher is free at the required time
            is_busy = any([
                True if at.period == asst.period and at.day == asst.day
                else False for at in at_list
            ])

            # Check if teacher has knowledge of the required subject
            has_subject_knowledge = t.assign_set.filter(
                subject=required_subject).exists()

            if not is_busy:
                if has_subject_knowledge:
                    ft_list.append(t)
                else:
                    teachers_without_knowledge.append(t)

        # Add warning message if no teachers available
        if not ft_list:
            messages.warning(request, _(
                FREE_TEACHERS_NO_AVAILABLE_TEACHERS_MESSAGE))

        return render(request, 'free_teachers.html', {
            'ft_list': ft_list,
            'required_subject': required_subject,
            'assignment_time': asst,
            'teachers_without_knowledge': teachers_without_knowledge,
            'total_teachers_checked': len(t_list),
            'available_teachers_count': len(ft_list)
        })


# Hiển thị danh sách các ngày đã điểm danh và tạo mới danh sách điểm danh theo ngày (nếu cần)
@login_required
def t_class_date(request, assign_id):
    assign = get_object_or_404(Assign, id=assign_id)
    now = timezone.now()
    att_list = assign.attendanceclass_set.all().order_by('-date')
    selected_assc = None
    class_obj = assign.class_id
    has_students = class_obj.student_set.exists()
    students = class_obj.student_set.all() if has_students else []
    
    # Thêm thống kê điểm danh cho mỗi buổi học
    att_list_with_stats = []
    for att_class in att_list:
        attendance_records = Attendance.objects.filter(
            attendanceclass=att_class, 
            subject=assign.subject
        )
        stats = _calculate_attendance_statistics(attendance_records)
        
        att_class.total_students = stats['total_students']
        att_class.present_students = stats['present_students']
        att_class.absent_students = stats['absent_students']
        att_class.attendance_percentage = stats['attendance_percentage']
        att_list_with_stats.append(att_class)

    if request.method == 'POST' and 'create_attendance' in request.POST:
        date_str = request.POST.get('attendance_date')
        try:
            attendance_date = timezone.datetime.strptime(
                date_str, DATE_FORMAT).date()
            if not AttendanceClass.objects.filter(assign=assign, date=attendance_date).exists():
                with transaction.atomic():
                    AttendanceClass.objects.create(
                        assign=assign,
                        date=attendance_date,
                        status=0  # Not Marked
                    )
            selected_assc = AttendanceClass.objects.get(
                assign=assign, date=attendance_date)
        except ValueError:
            messages.error(request, _(
                'Invalid date format. Please use YYYY-MM-DD.'))
            return redirect('t_class_date', assign_id=assign.id)

    elif request.method == 'POST' and 'confirm_attendance' in request.POST:
        assc_id = request.POST.get('assc_id')
        assc = get_object_or_404(AttendanceClass, id=assc_id)
        subject = assign.subject

        with transaction.atomic():
            for student in students:
                status_str = request.POST.get(student.USN)
                status = status_str == 'present'
                attendance_obj, created = Attendance.objects.get_or_create(
                    student=student,
                    subject=subject,
                    attendanceclass=assc,
                    date=assc.date,
                    defaults={'status': status}
                )
                if not created:
                    attendance_obj.status = status
                    attendance_obj.save()
            assc.status = 1  # Marked
            assc.save()
        messages.success(request, _('Attendance successfully recorded.'))
        return HttpResponseRedirect(reverse('t_class_date', args=(assign.id,)))

    elif request.method == 'POST' and 'select_attendance' in request.POST:
        assc_id = request.POST.get('assc_id')
        selected_assc = get_object_or_404(AttendanceClass, id=assc_id)

    # Thêm thông tin chi tiết về lớp học
    class_info = {
        'class_id': class_obj.id,
        'department': class_obj.dept.name,
        'section': class_obj.section,
        'semester': class_obj.sem,
        'total_students': len(students),
        'subject': assign.subject.name,
        'subject_code': assign.subject.id,
        'teacher': assign.teacher.name,
    }

    context = {
        'assign': assign,
        'att_list': att_list_with_stats,
        'today': now.date(),
        'selected_assc': selected_assc,
        'c': class_obj,
        'has_students': has_students,
        'students': students,
        'class_info': class_info,
    }
    return render(request, 't_class_date.html', context)

# Thông tin điểm danh


@login_required
def t_attendance(request, ass_c_id):
    assc = get_object_or_404(AttendanceClass, id=ass_c_id)
    assign = assc.assign
    class_obj = assign.class_id
    students = class_obj.student_set.all()
    total_students_in_class = students.count()
    
    # Thêm thông tin chi tiết về lớp học
    class_info = {
        'class_id': class_obj.id,
        'department': class_obj.dept.name,
        'section': class_obj.section,
        'semester': class_obj.sem,
        'total_students': total_students_in_class,
        'subject': assign.subject.name,
        'subject_code': assign.subject.id,
        'teacher': assign.teacher.name,
        'date': assc.date,
    }

    context = {
        'ass': assign,
        'c': class_obj,
        'assc': assc,
        'students': students,
        'total_students_in_class': total_students_in_class,
        'class_info': class_info,
    }
    return render(request, 't_attendance.html', context)

# View xử lý xác nhận điểm danh


@login_required
def confirm(request, ass_c_id):
    assc = get_object_or_404(AttendanceClass, id=ass_c_id)
    assign = assc.assign
    subject = assign.subject
    class_obj = assign.class_id
    has_students = class_obj.student_set.exists()  # Check if students exist
    students = class_obj.student_set.all() if has_students else [
    ]  # Fetch students only if needed

    with transaction.atomic():
        for student in students:
            status_str = request.POST.get(student.USN)
            status = status_str == 'present'
            attendance_obj, created = Attendance.objects.get_or_create(
                student=student,
                subject=subject,
                attendanceclass=assc,
                date=assc.date,
                defaults={'status': status}
            )
            if not created:
                attendance_obj.status = status
                attendance_obj.save()
        assc.status = 1  # Marked
        assc.save()

    messages.success(request, _('Attendance successfully recorded.'))
    return HttpResponseRedirect(reverse('t_class_date', args=(assc.assign.id,)))

# View hiển thị giao diện chỉnh sửa điểm danh


@login_required
def edit_att(request, ass_c_id):
    assc = get_object_or_404(AttendanceClass, id=ass_c_id)
    assign = assc.assign
    subject = assign.subject
    att_list = Attendance.objects.filter(attendanceclass=assc, subject=subject)
    class_obj = assign.class_id
    
    # Thêm thông tin chi tiết về lớp học và thống kê
    stats = _calculate_attendance_statistics(att_list)
    
    context = {
        'assc': assc,
        'att_list': att_list,
        'assign': assign,
        'class_obj': class_obj,
        'total_students': stats['total_students'],
        'present_students': stats['present_students'],
        'absent_students': stats['absent_students'],
    }
    return render(request, 't_edit_att.html', context)

# View hiển thị danh sách điểm danh


@login_required
def view_att(request, ass_c_id):
    assc = get_object_or_404(AttendanceClass, id=ass_c_id)
    assign = assc.assign
    subject = assign.subject
    att_list = Attendance.objects.filter(attendanceclass=assc, subject=subject)
    class_obj = assign.class_id
    
    # Tính toán thống kê điểm danh
    stats = _calculate_attendance_statistics(att_list)
    
    # Thêm thông tin chi tiết về lớp học
    class_info = {
        'class_id': class_obj.id,
        'department': class_obj.dept.name,
        'section': class_obj.section,
        'semester': class_obj.sem,
        'subject': assign.subject.name,
        'subject_code': assign.subject.id,
        'teacher': assign.teacher.name,
        'date': assc.date,
    }
    
    context = {
        'assc': assc,
        'att_list': att_list,
        'assign': assign,
        'total_students': stats['total_students'],
        'present_students': stats['present_students'],
        'absent_students': stats['absent_students'],
        'attendance_percentage': stats['attendance_percentage'],
        'class_info': class_info,
    }
    return render(request, 't_view_att.html', context)

#hiển thị báo cáo học tập của học sinh trong một lớp học cụ thể.

@login_required()
def t_report(request, assign_id):
    ass = get_object_or_404(Assign, id=assign_id)
    sc_list = []
    
    # Get class information
    class_obj = ass.class_id
    subject_obj = ass.subject
    
    # Statistics counters
    # Đếm học sinh có điểm danh tốt (≥75%)
    good_attendance_count = 0
    # Đếm học sinh có CIE đạt chuẩn (≥25)
    good_cie_count = 0
    # Đếm học sinh cần hỗ trợ (điểm danh <75% HOẶC CIE <25)
    need_support_count = 0
    
    for stud in class_obj.student_set.all():
        student_subjects = StudentSubject.objects.filter(student=stud, subject=subject_obj)
        if student_subjects.exists():
            # If student is registered for this subject, add to list
            student_subject = student_subjects.first()
            sc_list.append(student_subject)
            
            # Calculate statistics with error handling
            try:
                attendance = student_subject.get_attendance()
            except:
                attendance = 0
                
            try:
                cie = student_subject.get_cie()
            except:
                cie = 0
            
            # Count statistics
            if attendance >= ATTENDANCE_STANDARD:
                good_attendance_count += 1
            if cie >= CIE_STANDARD:
                good_cie_count += 1
            if attendance < ATTENDANCE_STANDARD or cie < CIE_STANDARD:
                need_support_count += 1
    
    # Calculate pass rate
    total_students = len(sc_list)
    pass_rate = 100 if total_students == 0 else round((total_students - need_support_count) / total_students * 100)
    
    context = {
        'sc_list': sc_list,
        'class_obj': class_obj,
        'subject_obj': subject_obj,
        'assignment': ass,
        'good_attendance_count': good_attendance_count,
        'good_cie_count': good_cie_count,
        'need_support_count': need_support_count,
        'pass_rate': pass_rate,
        'ATTENDANCE_STANDARD': ATTENDANCE_STANDARD,
        'CIE_STANDARD': CIE_STANDARD,
        'attendance_success_label': f"≥{ATTENDANCE_STANDARD}%",
        'attendance_danger_label': f"<{ATTENDANCE_STANDARD}%",
        'cie_success_label': f"≥{CIE_STANDARD}",
        'cie_danger_label': f"<{CIE_STANDARD}",
    }
    
    return render(request, 't_report.html', context)

@login_required
def view_students(request, assign_id):
    """
    View danh sách sinh viên và điểm tổng của họ trong một assignment
    """
    assignment = get_object_or_404(Assign, id=assign_id)
    
    # Kiểm tra xem user hiện tại có phải là giáo viên của assignment này không
    if hasattr(assignment.teacher, 'user') and assignment.teacher.user and assignment.teacher.user != request.user:
        messages.error(request, _('Bạn không có quyền truy cập assignment này!'))
        return redirect('teacher_dashboard')
    
    # Lấy danh sách sinh viên trong lớp
    students = assignment.class_id.student_set.all().order_by('name')
    
    # Lấy thông tin điểm và điểm danh cho từng sinh viên
    students_data = []
    for student in students:
        # Kiểm tra xem sinh viên có đăng ký môn học này không
        try:
            student_subject = StudentSubject.objects.get(
                student=student,
                subject=assignment.subject
            )
            
            # Lấy tất cả điểm của sinh viên
            marks = student_subject.marks_set.all().order_by('name')
            total_marks = sum(mark.marks1 for mark in marks)
            
            # Lấy thông tin điểm danh
            attendance_records = Attendance.objects.filter(
                student=student,
                subject=assignment.subject
            )
            total_classes = attendance_records.count()
            attended_classes = attendance_records.filter(status=True).count()
            attendance_percentage = round((attended_classes / total_classes * 100), 2) if total_classes > 0 else 0
            
            # Tính CIE
            marks_list = [mark.marks1 for mark in marks]
            cie_score = math.ceil(sum(marks_list[:CIE_CALCULATION_LIMIT]) / CIE_DIVISOR) if marks_list else 0
            
        except StudentSubject.DoesNotExist:
            # Sinh viên chưa đăng ký môn học
            marks = []
            total_marks = 0
            attendance_percentage = 0
            cie_score = 0
            total_classes = 0
            attended_classes = 0
        
        students_data.append({
            'student': student,
            'marks': marks,
            'total_marks': total_marks,
            'attendance_percentage': attendance_percentage,
            'cie_score': cie_score,
            'total_classes': total_classes,
            'attended_classes': attended_classes,
            'is_registered': hasattr(locals(), 'student_subject'),
        })
    
    # Pagination
    from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
    paginator = Paginator(students_data, 25)  # 25 students per page
    page = request.GET.get('page')
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)
    
    context = {
        'assignment': assignment,
        'students_page': students_page,
        'students_total': len(students_data),
        'class_obj': assignment.class_id,
        'subject': assignment.subject,
    }
    
    return render(request, 't_view_students.html', context)

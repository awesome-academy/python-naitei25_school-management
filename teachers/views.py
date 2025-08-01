from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Teacher, Assign, ExamSession, Marks
from students.models import StudentSubject
from django.db import transaction
# Create your views here.

@login_required
def index(request):
    if request.user.is_teacher:
        return render(request, 't_homepage.html')


# Teacher Views
#Hiển thị thông tin lớp học hoặc các lựa chọn liên quan đến giáo viên.
@login_required
def t_clas(request, teacher_id, choice):
    teacher1 = get_object_or_404(Teacher, id=teacher_id)
    return render(request, 't_clas.html', {'teacher1': teacher1, 'choice': choice})

#Hiển thị danh sách các phiên thi (ExamSession) của một assignment (môn học/lớp/giáo viên).
@login_required
def t_marks_list(request, assign_id):
    assignment = get_object_or_404(Assign, id=assign_id)
    exam_sessions_list = ExamSession.objects.filter(assign=assignment)
    return render(request, 't_marks_list.html', {'m_list': exam_sessions_list})

#Hiển thị form nhập điểm cho các học sinh đang học môn học này trong lớp.
# Chỉ hiển thị học sinh đã đăng ký môn học (StudentSubject).
@login_required()
def t_marks_entry(request, marks_c_id):
    with transaction.atomic():
        exam_session = get_object_or_404(ExamSession, id=marks_c_id)
        assignment = exam_session.assign
        subject = assignment.subject
        class_obj = assignment.class_id
    
        # Lấy các học sinh đang học môn này trong lớp này
        students_in_subject = StudentSubject.objects.filter(
            subject=subject,
            student__class_id=class_obj
        ).select_related('student')

        context = {
            'ass': assignment,
            'c': class_obj,
            'mc': exam_session,
            'students_in_subject': students_in_subject,
        }
        return render(request, 't_marks_entry.html', context)

#Xử lý dữ liệu điểm số được nhập từ form.
# Lưu điểm cho từng học sinh vào database.
# Đánh dấu trạng thái phiên thi là đã hoàn thành.
@login_required()
def marks_confirm(request, marks_c_id):
    with transaction.atomic():
        exam_session = get_object_or_404(ExamSession, id=marks_c_id)
        assignment = exam_session.assign
        subject = assignment.subject
        class_object = assignment.class_id

        students_in_subject = StudentSubject.objects.filter(
            subject=subject,
            student__class_id=class_object
        ).select_related('student')

        for student_subject in students_in_subject:
            student = student_subject.student
            student_mark = request.POST[student.USN]
            student_subject = StudentSubject.objects.get(subject=subject, student=student)
            marks_instance,_ = student_subject.marks_set.get_or_create(name=exam_session.name)
            marks_instance.marks1 = student_mark
            marks_instance.save()
        exam_session.status = True
        exam_session.save()

    return HttpResponseRedirect(reverse('t_marks_list', args=(assignment.id,)))

#Hiển thị form để chỉnh sửa điểm của các học sinh đang học môn học này trong lớp.
# Chỉ hiển thị học sinh đã đăng ký môn học (StudentSubject).
# Cho phép giáo viên cập nhật lại điểm số đã nhập.
@login_required()
def edit_marks(request, marks_c_id):
    with transaction.atomic():
        exam_session = get_object_or_404(ExamSession, id=marks_c_id)
        subject = exam_session.assign.subject
        class_object = exam_session.assign.class_id

        # Lấy các StudentSubject của học sinh thuộc lớp này và đăng ký môn này
        students_in_subject = StudentSubject.objects.filter(
            subject=subject,
            student__class_id=class_object
        ).select_related('student')

        marks_list = []
        for student_subject in students_in_subject:
            try:
                marks_instance = student_subject.marks_set.get(name=exam_session.name)
                marks_list.append(marks_instance)
            except Marks.DoesNotExist:
                # Bỏ qua hoặc xử lý trường hợp không có điểm
                pass
        context = {
            'mc': exam_session,
            'm_list': marks_list,
        }
        return render(request, 'edit_marks.html', context)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Teacher, Assign, ExamSession
from students.models import StudentSubject
# Create your views here.

@login_required
def index(request):
    if request.user.is_teacher:
        return render(request, 't_homepage.html')


# Teacher Views

@login_required
def t_clas(request, teacher_id, choice):
    teacher1 = get_object_or_404(Teacher, id=teacher_id)
    return render(request, 't_clas.html', {'teacher1': teacher1, 'choice': choice})

@login_required
def t_marks_list(request, assign_id):
    assignment = get_object_or_404(Assign, id=assign_id)
    exam_sessions_list = ExamSession.objects.filter(assign=assignment)
    return render(request, 't_marks_list.html', {'m_list': exam_sessions_list})

@login_required()
def t_marks_entry(request, marks_c_id):
    exam_session = get_object_or_404(ExamSession, id=marks_c_id)
    assignment = exam_session.assign
    class_obj = assignment.class_id
    context = {
        'ass': assignment,
        'c': class_obj,
        'mc': exam_session,
    }
    return render(request, 't_marks_entry.html', context)

@login_required()
def marks_confirm(request, marks_c_id):
    exam_session = get_object_or_404(ExamSession, id=marks_c_id)
    assignment = exam_session.assign
    subject = assignment.subject
    class_obj = assignment.class_id
    
    for student in class_obj.student_set.all():
        student_mark = request.POST[student.USN]
        
        # Check if StudentSubject exists, create if not
        student_subject, student_subject_created = StudentSubject.objects.get_or_create(
            subject=subject, 
            student=student
        )
        
        # Check if Marks exists, create if not
        marks_object, marks_created = student_subject.marks_set.get_or_create(
            name=exam_session.name
        )
        
        marks_object.marks1 = student_mark
        marks_object.save()
    
    exam_session.status = True
    exam_session.save()

    return HttpResponseRedirect(reverse('t_marks_list', args=(assignment.id,)))

@login_required()
def edit_marks(request, marks_c_id):
    exam_session = get_object_or_404(ExamSession, id=marks_c_id)
    subject = exam_session.assign.subject
    students_list = exam_session.assign.class_id.student_set.all()
    marks_list = []
    
    for student in students_list:
        student_subject = StudentSubject.objects.get(subject=subject, student=student)
        marks_object = student_subject.marks_set.get(name=exam_session.name)
        marks_list.append(marks_object)
    
    context = {
        'mc': exam_session,
        'm_list': marks_list,
    }
    return render(request, 'edit_marks.html', context)


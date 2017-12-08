from django.shortcuts import render, HttpResponseRedirect, resolve_url
from lsoa.models import Course, Student
from django.contrib.auth.decorators import login_required

@login_required
def default_homepage(request):
    # If it's a teacher, redirect to a class
    classes = request.user.teacher_courses.order_by('-created')
    return HttpResponseRedirect(resolve_url('view_course', classes.first().id))


@login_required
def view_course(request, course_id):
    course = Course.objects.get(id=course_id)
    data = {
        'course': course,
        'all_classes': request.user.teacher_courses.order_by('-created').all()
    }
    return render(request, 'course.html', data)

from django.contrib.auth import get_user_model
from django.db import models


class Course(models.Model):
    """
    A single class
    """

    name = models.CharField(max_length=100, null=False, blank=False)
    # students = models.ManyToManyField(get_user_model(), related_name='student_courses')
    # todo students never log in, no need to make them users
    teachers = models.ManyToManyField(get_user_model(), related_name='teacher_courses')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        for student in self.students:
            # TODO: Validate each student only added once & user is student
            pass
        for teacher in self.teachers:
            # TODO: Validate each teacher only added once & user is teacher
            pass

from django.db import models
from django.contrib.auth.models import User as AuthUser
import reversion


@reversion.register()
class Course(models.Model):
    """
    A single class
    """

    name = models.CharField(max_length=100, null=False, blank=False)
    students = models.ManyToManyField(AuthUser, related_name='student_courses')
    teachers = models.ManyToManyField(AuthUser, related_name='teacher_courses')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        for student in self.students:
            # TODO: Validate each student only added once & user is student
            pass
        for teacher in self.teachers:
            # TODO: Validate each teacher only added once & user is teacher
            pass

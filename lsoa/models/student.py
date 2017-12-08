from django.db import models
from model_utils.models import TimeStampedModel


class Student(TimeStampedModel):
    """
    A single student
    """

    first_name = models.CharField(max_length=100, null=False, blank=False)
    last_name = models.CharField(max_length=100, null=False, blank=False)
    nickname = models.CharField(max_length=100, null=False, blank=False, help_text="Used to help differentiate students with the same name")

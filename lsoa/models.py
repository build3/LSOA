import os
from uuid import uuid4

from django.db import models
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django_extensions.db.models import TimeStampedModel
from tinymce.models import HTMLField

from utils.ownership import OwnerMixin


@deconstructible
class UploadToPathAndRename(object):

    def __init__(self, path):
        self.sub_path = path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # get filename
        filename = '{}.{}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(self.sub_path, filename)


class Course(TimeStampedModel, OwnerMixin):
    name = models.CharField(max_length=255)
    students = models.ManyToManyField('lsoa.Student', blank=True)

    def __str__(self):
        return self.name


class Student(TimeStampedModel):
    """
    A Student has associated data, however on the Student record itself, simply
    record their name.
    """
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return '{} {} '.format(self.nickname, self.last_name[0]) if self.nickname else \
            '{} {}'.format(self.first_name, self.last_name[0])


class StudentGroup(TimeStampedModel):
    """
    A StudentGroup is a container model for students of a course in a group. A
    student can be in multiple groups at the same time but only one group for a
    particular StudentGrouping.
    """
    name = models.CharField(max_length=255, blank=True, default='')  # optional
    course = models.ForeignKey('lsoa.Course', on_delete=models.CASCADE)
    students = models.ManyToManyField('lsoa.Student', blank=True)

    def __str__(self):
        return self.name if self.name else ', '.join(str(student) for student in self.students.all())


class StudentGrouping(TimeStampedModel):
    """
    A StudentGrouping is a collection of student groups. This is convenient because
    a teacher might say "get in your big groups" where students are in groups of 4-5
    versus "pair up with your study buddy" to put students in pairs.
    """
    name = models.CharField(max_length=255)
    course = models.ForeignKey('lsoa.Course', on_delete=models.CASCADE)
    groups = models.ManyToManyField('lsoa.StudentGroup', blank=True)

    def __str__(self):
        return '{} [{}]'.format(self.name, self.course)


class Observation(TimeStampedModel, OwnerMixin):
    """
    An Observation is a "snapshot in time" of student(s) exhibiting mastery of
    a certain (or multiple) learning constructs, paired with typed notes or
    visual evidence (picture or video).
    """
    # if an observation is checked with "use previous observation", use this to denote which one
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.PROTECT)

    # regardless of how they're grouped, just save the raw students to the observation
    students = models.ManyToManyField('lsoa.Student', blank=True)
    constructs = models.ManyToManyField('lsoa.LearningConstructSublevel', blank=True)
    tags = models.ManyToManyField('lsoa.ContextTag', blank=True)

    # save the original and annotated image. If we save the annotated image, we can use it again
    # in the next observation.
    annotated_image = models.FileField(blank=True, null=True)
    original_image = models.FileField(blank=True, null=True)
    video = models.FileField(blank=True, null=True)

    # the end user can type notes or take an AV sample and just talk into the mic
    notes = models.TextField(blank=True)
    video_notes = models.FileField(blank=True, null=True)

    def __str__(self):
        return 'Observation at {}'.format(self.created)


class LearningConstruct(TimeStampedModel):
    """
    A LearningConstruct is a ...
    """
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    def __str__(self):
        return '{} ({})'.format(self.name, self.abbreviation)


class LearningConstructLevel(TimeStampedModel):
    """
    Some description here...
    """
    construct = models.ForeignKey('lsoa.LearningConstruct', on_delete=models.CASCADE)
    level = models.IntegerField()
    description = models.TextField()

    def __str__(self):
        return '{} {}'.format(self.construct.abbreviation, self.level)

    class Meta:
        ordering = ['level']


class LearningConstructSublevel(TimeStampedModel):
    """
    Some description here...
    """
    level = models.ForeignKey('lsoa.LearningConstructLevel', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        ordering = ['name']


class LearningConstructSublevelExample(TimeStampedModel):
    """
    An example that goes in the bottom-center help box. Selecting/deselecting a sublevel (the blue/white tags on the
    bottom left of the observation panel) will cause this box (as well as the description box) to populate with the
    proper content.
    """
    sublevel = models.ForeignKey('lsoa.LearningConstructSublevel', related_name='examples', on_delete=models.CASCADE)
    text = HTMLField()
    image = models.ImageField(upload_to=UploadToPathAndRename('example_images/'), blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return '({}) {}'.format(self.sublevel.name, self.text[:50])


class ContextTag(TimeStampedModel, OwnerMixin):
    """
    A context tag for tagging observations
    """
    text = models.CharField(max_length=255)
    last_used = models.DateTimeField(auto_now=True)

    def use(self):
        self.last_used = timezone.now()
        self.save()
        return self

    class Meta:
        ordering = ['-last_used']

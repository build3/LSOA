import json
import os
from uuid import uuid4

from django.contrib.postgres.fields import ArrayField
from django.db import models, transaction
from django.utils import timezone
from django.utils.deconstruct import deconstructible
from django.utils.timezone import now
from django_extensions.db.models import TimeStampedModel
from tinymce.models import HTMLField

from utils.ownership import OwnerMixin, OptionalOwnerMixin


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
    students = models.ManyToManyField('kidviz.Student', blank=True)
    grade_level = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name


class Student(TimeStampedModel):
    """
    A Student has associated data, however on the Student record itself, simply
    record their name.
    """
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    STUDENT_STATUSES = (
        (ACTIVE, 'active'),
        (INACTIVE, 'inactive')
    )

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    nickname = models.CharField(max_length=255, blank=True, default='')
    grade_level = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(max_length=30, choices=STUDENT_STATUSES, default=ACTIVE)
    consented_to_research = models.BooleanField(default=False)

    def __str__(self):
        return '{} {}'.format(self.nickname or self.first_name, self.last_name[0])

    def advance_grade_level(self):
        self.grade_level += 1
        self.save()

    @property
    def name(self):
        return self.first_name + ' ' + self.last_name

    def save(self, **kwargs):
        # this keeps excel import from bombing on nulls
        self.nickname = self.nickname or ''
        return super().save(**kwargs)

    @transaction.atomic
    def reassign(self, other):
        """
        Reasign related entry with other studet to self.
        """
        if self == other:
            return

        models = [Course, Observation, StudentGroup]

        for model in models:
            entries = model.objects.filter(students__in=[other])
            for entry in entries:
                entry.students.remove(other)
                if not self in entry.students.all():
                    entry.students.add(self)

    @transaction.atomic
    def split_to_new(self, course):
        # Create copy of student, but don't copy nickname and student_id.
        new_student = Student.objects.create(
            first_name=self.first_name,
            last_name=self.last_name,
            grade_level=self.grade_level,
            status=self.ACTIVE
        )

        course.students.remove(self)
        course.students.add(new_student)

        observations = Observation.objects.filter(students__in=[self], course=course)
        for observation in observations:
            observation.students.remove(self)
            observation.students.add(new_student)

        groups = StudentGroup.objects.filter(students__in=[self], course=course)
        for group in groups:
            group.students.remove(self)
            group.students.add(new_student)

        return new_student


class StudentGroup(TimeStampedModel):
    """
    A StudentGroup is a container model for students of a course in a group. A
    student can be in multiple groups at the same time but only one group for a
    particular StudentGrouping.
    """
    name = models.CharField(max_length=255, blank=True, default='')  # optional
    course = models.ForeignKey('kidviz.Course', on_delete=models.CASCADE)
    students = models.ManyToManyField('kidviz.Student', blank=True)

    def __str__(self):
        return self.name if self.name else ', '.join(str(student) for student in self.students.all())


class StudentGrouping(TimeStampedModel):
    """
    A StudentGrouping is a collection of student groups. This is convenient because
    a teacher might say "get in your big groups" where students are in groups of 4-5
    versus "pair up with your study buddy" to put students in pairs.
    """
    name = models.CharField(max_length=255)
    course = models.ForeignKey('kidviz.Course', on_delete=models.CASCADE)
    groups = models.ManyToManyField('kidviz.StudentGroup', blank=True)

    def __str__(self):
        return '{}'.format(self.name)


class Observation(TimeStampedModel, OwnerMixin):
    """
    An Observation is a "snapshot in time" of student(s) exhibiting mastery of
    a certain (or multiple) learning constructs, paired with typed notes or
    visual evidence (picture or video).
    """
    # if an observation is checked with "use previous observation", use this to denote which one
    name = models.CharField(max_length=75, blank=True, default='')
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.PROTECT)

    # Field describes if constructs selection is required.
    no_constructs = models.BooleanField(default=False)

    course = models.ForeignKey('kidviz.Course', blank=True, null=True, on_delete=models.PROTECT)
    grouping = models.ForeignKey('kidviz.StudentGrouping', blank=True, null=True, on_delete=models.SET_NULL)
    construct_choices = ArrayField(base_field=models.PositiveIntegerField(), null=True, blank=True, default=[])
    tag_choices = ArrayField(base_field=models.PositiveIntegerField(), null=True, blank=True, default=[])

    # since focus is assigned per-observation, ih has to be stored here and not on the tag's side
    curricular_focus = models.CharField(max_length=255, blank=True, null=True)

    # regardless of how they're grouped, just save the raw students to the observation
    students = models.ManyToManyField('kidviz.Student', blank=True)
    constructs = models.ManyToManyField('kidviz.LearningConstructSublevel', blank=True)
    tags = models.ManyToManyField('kidviz.ContextTag', blank=True)

    # save the original and annotated image. If we save the annotated image, we can use it again
    # in the next observation.
    annotation_data = models.TextField(default='', null=True, blank=True)
    original_image = models.FileField(upload_to=UploadToPathAndRename('original_images/'), blank=True, null=True)
    video = models.FileField(upload_to=UploadToPathAndRename('videos/'), blank=True, null=True)

    # the end user can type notes or take an AV sample and just talk into the mic
    notes = models.TextField(blank=True)
    video_notes = models.FileField(upload_to=UploadToPathAndRename('video_notes/'), blank=True, null=True)

    observation_date = models.DateField(default=now)
    is_draft = models.BooleanField(default=False)

    @property
    def allowed_students(self):
        if not self.grouping:
            return []

        groups = self.grouping.groups.all()
        students = set()
        for group in groups:
            students.update(list(group.students.all()))

        return list(students)

    def update_draft_media(self, image, video):
        """Updates media for `Observation`.

        Args:
            image(File or None): `original_image` from request.
            video(File or None): `video` from request.
        """
        if self.video and image:
            self.video = None
            self.save()

        if self.original_image and video:
            self.original_image = None
            self.save()

    def reset_media(self):
        """Reset `video` and `original_image` for `Observation`."""
        self.video = None
        self.original_image = None
        self.save()

    def __str__(self):
        _display = self.name or 'Observation at {}'.format(self.created)
        return _display


class LearningConstruct(TimeStampedModel):
    """
    A LearningConstruct is a ...
    """
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)

    def __str__(self):
        return '{} ({})'.format(self.name, self.abbreviation)

    @property
    def sublevels(self):
        return LearningConstructSublevel.objects.filter(
            level__construct_id=self.id
        )


class LearningConstructLevel(TimeStampedModel):
    """
    Some description here...
    """
    construct = models.ForeignKey('kidviz.LearningConstruct', on_delete=models.CASCADE, related_name='levels')
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
    level = models.ForeignKey('kidviz.LearningConstructLevel', on_delete=models.CASCADE, related_name='sublevels')
    name = models.CharField(max_length=255)
    description = models.TextField()

    def short_name(self):
        try:
            return '{}'.format(self.name.split()[1])
        except:
            return '{}'.format(self.name)

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
    sublevel = models.ForeignKey('kidviz.LearningConstructSublevel', related_name='examples', on_delete=models.CASCADE)
    text = HTMLField()
    image = models.ImageField(upload_to=UploadToPathAndRename('example_images/'), blank=True, null=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return '({}) {}'.format(self.sublevel.name, self.text[:50])


class ContextTag(TimeStampedModel, OptionalOwnerMixin):
    """
    A context tag for tagging observations
    """
    text = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#17a2b8')
    last_used = models.DateTimeField(auto_now=True)
    curricular_focus = models.BooleanField(default=False)

    def __str__(self):
        return self.text

    def use(self):
        self.last_used = timezone.now()
        self.save()
        return self

    class Meta:
        ordering = ['-last_used']


class AdminPerms(models.Model):
    class Meta:
        managed = False  # No database table creation or deletion operations will be performed for this model

        permissions = (
            ('can_approve_deny_users', 'Can Approve or Deny Users'),
        )

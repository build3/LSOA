from django.utils import timezone
from tablib import Dataset

from lsoa.models import Course, Student
from import_export.formats import base_formats

FILE_FORMAT_MAP = {
    'xlsx': base_formats.XLSX,
    'xls': base_formats.XLS,
    'csv': base_formats.CSV,
}

ACCEPTED_FILE_EXTENSIONS = FILE_FORMAT_MAP.keys()
ACCEPTED_FILE_FORMATS = FILE_FORMAT_MAP.values()


def do_data_clean(table):

    def clean_string(cell):
        return str(cell or '').strip()

    data = table or []
    for row in data:
        for column, value in row.items():
            if isinstance(value, str):
                row[column] = clean_string(value)

    return data


class ClassRoster(object):

    COLUMN_ORDER = (
        'Course ID',
        'Course Name',
        'Grade Level',
        'Student ID',
        'Student Last Name',
        'Student First Name',
        'Student Nickname',
    )

    def __init__(self, user):
        self.owner = user

    def empty_dataset(self):
        dataset = Dataset()
        dataset.headers = self.COLUMN_ORDER
        return dataset

    def preview_rows(self, dataset):
        imported_data = do_data_clean(dataset.dict)
        try:
            for row in imported_data:
                if not row.get('Course ID'):
                    # todo: should owner be part of filter?  should owner be a file column?
                    course = Course.objects.filter(name__iexact=row.get('Course Name'),
                                                   grade_level=row.get('Grade Level', 0)).order_by('-created').first()
                    if course:
                        row['Course ID'] = course.id
                    else:
                        row['Course ID'] = 'NEW'

                if not row.get('Student ID'):
                    student = Student.objects.filter(last_name__iexact=row['Student Last Name'],
                                                     first_name__iexact=row['Student First Name'],
                                                     grade_level=int(row.get('Grade Level', 0))).first()
                    if student:
                        row['Student ID'] = student.student_id
                    else:
                        raise AttributeError('Student ID is required for new students')

            preview_data = Dataset()
            preview_data.dict = imported_data
            return preview_data

        except KeyError as err:
            raise KeyError('The file is missing a required column. {}'.format(err))

    def process_rows(self, dataset):
        imported_data = dataset.dict
        course_name = ''
        course = None
        students = []

        for row in imported_data:
            if not course_name or course_name != row['Course Name']:
                if students and course:
                    course.students.set(students)
                    course.save()
                students = []
                course_name = row['Course Name']
                if row['Course ID'] == 'NEW':
                    course, created = Course.objects.get_or_create(name=row['Course Name'],
                                                                   grade_level=int(row.get('Grade Level', 0)),
                                                                   defaults={'owner': self.owner})
                else:
                    course, created = Course.objects.get(id=int(row['Course ID'])), False

            row['Course ID'] = course.id

            student_id = row['Student ID']
            try:
                student = Student.objects.get(student_id=student_id)
            except Student.DoesNotExist:
                student = Student.objects.create(
                    last_name=row['Student Last Name'],
                    first_name=row['Student First Name'],
                    grade_level=int(row.get('Grade Level', 0)),
                    student_id=row['Student ID'],
                    nickname=row['Student Nickname']
                )

            row['Student ID'] = student.student_id
            students.append(student.id)

        if students and course:
            course.students.set(students)
            course.save()

    def build_rows(self, queryset):
        dataset = self.empty_dataset()
        for course in queryset:
            course_id = course.id
            course_name = course.name
            grade_level = course.grade_level
            students = course.students.all()
            if students:
                for student in students:
                    # field order matters and must match COLUMN_ORDER constant
                    row = [course_id, course_name, grade_level,
                           student.id, student.last_name, student.first_name, student.nickname]
                    dataset.append(row)
            else:
                # field order matters and must match COLUMN_ORDER constant
                # this will output a course that has no students
                row = [course_id, course_name, grade_level,
                       '', '', '', '', ]
                dataset.append(row)

        return dataset

    @classmethod
    def export(cls, user, queryset, fmt='csv'):
        from django.http import HttpResponse

        dataset = cls(user=user).build_rows(queryset)
        dataset.title = 'Class Roster'
        file_name = 'LSOA Class Roster {}'.format(timezone.now().strftime('%Y%m%d'))
        exported_data = dataset.export(format=fmt)
        response = HttpResponse(exported_data)
        response['Content-Disposition'] = 'attachment; filename={}.{}'.format(file_name, fmt)
        return response

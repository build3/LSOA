from django.contrib.auth.management import create_permissions
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations

def create_groups_and_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    teachers, _ = Group.objects.get_or_create(name='Teachers')
    administrators, _ = Group.objects.get_or_create(name='Administrators')

    Course = apps.get_model('lsoa', 'Course')
    Student = apps.get_model('lsoa', 'Student')
    StudentGroup = apps.get_model('lsoa', 'StudentGroup')
    StudentGrouping = apps.get_model('lsoa', 'StudentGrouping')
    Observation = apps.get_model('lsoa', 'Observation')
    LearningConstruct = apps.get_model('lsoa', 'LearningConstruct')

    Permission = apps.get_model('auth', 'Permission')

    emit_post_migrate_signal(2, False, 'default')  # this creates permissions

    teachers.permissions.add(Permission.objects.get(codename='add_course'))
    teachers.permissions.add(Permission.objects.get(codename='change_course'))
    teachers.permissions.add(Permission.objects.get(codename='delete_course'))
    administrators.permissions.add(Permission.objects.get(codename='add_course'))
    administrators.permissions.add(Permission.objects.get(codename='change_course'))
    administrators.permissions.add(Permission.objects.get(codename='delete_course'))

    teachers.permissions.add(Permission.objects.get(codename='add_observation'))
    teachers.permissions.add(Permission.objects.get(codename='change_observation'))
    teachers.permissions.add(Permission.objects.get(codename='delete_observation'))
    administrators.permissions.add(Permission.objects.get(codename='add_observation'))
    administrators.permissions.add(Permission.objects.get(codename='change_observation'))
    administrators.permissions.add(Permission.objects.get(codename='delete_observation'))

    teachers.permissions.add(Permission.objects.get(codename='add_studentgrouping'))
    teachers.permissions.add(Permission.objects.get(codename='change_studentgrouping'))
    teachers.permissions.add(Permission.objects.get(codename='delete_studentgrouping'))
    administrators.permissions.add(Permission.objects.get(codename='add_observation'))
    administrators.permissions.add(Permission.objects.get(codename='change_observation'))
    administrators.permissions.add(Permission.objects.get(codename='delete_observation'))

    teachers.permissions.add(Permission.objects.get(codename='add_studentgroup'))
    teachers.permissions.add(Permission.objects.get(codename='change_studentgroup'))
    teachers.permissions.add(Permission.objects.get(codename='delete_studentgroup'))
    administrators.permissions.add(Permission.objects.get(codename='add_observation'))
    administrators.permissions.add(Permission.objects.get(codename='change_observation'))
    administrators.permissions.add(Permission.objects.get(codename='delete_observation'))

    teachers.permissions.add(Permission.objects.get(codename='add_student'))
    teachers.permissions.add(Permission.objects.get(codename='change_student'))
    teachers.permissions.add(Permission.objects.get(codename='delete_student'))
    administrators.permissions.add(Permission.objects.get(codename='add_student'))
    administrators.permissions.add(Permission.objects.get(codename='change_student'))
    administrators.permissions.add(Permission.objects.get(codename='delete_student'))

    administrators.permissions.add(Permission.objects.get(codename='add_learningconstruct'))
    administrators.permissions.add(Permission.objects.get(codename='change_learningconstruct'))
    administrators.permissions.add(Permission.objects.get(codename='delete_learningconstruct'))


class Migration(migrations.Migration):
    dependencies = [
        ('lsoa', '0001_initial'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions)
    ]

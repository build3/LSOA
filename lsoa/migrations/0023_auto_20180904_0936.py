# Generated by Django 2.0.4 on 2018-09-04 09:36

from django.db import migrations


def add_permissions(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    teachers, _ = Group.objects.get_or_create(name='Teachers')
    administrators, _ = Group.objects.get_or_create(name='Administrators')
    Permission = apps.get_model('auth', 'Permission')

    # these 6 perms were screwed up in the 0002 migration
    administrators.permissions.add(Permission.objects.get(codename='add_studentgrouping'))
    administrators.permissions.add(Permission.objects.get(codename='change_studentgrouping'))
    administrators.permissions.add(Permission.objects.get(codename='delete_studentgrouping'))
    administrators.permissions.add(Permission.objects.get(codename='add_studentgroup'))
    administrators.permissions.add(Permission.objects.get(codename='change_studentgroup'))
    administrators.permissions.add(Permission.objects.get(codename='delete_studentgroup'))

    # these 9 perms need to be added so that administrators can change these things
    administrators.permissions.add(Permission.objects.get(codename='add_learningconstructlevel'))
    administrators.permissions.add(Permission.objects.get(codename='change_learningconstructlevel'))
    administrators.permissions.add(Permission.objects.get(codename='delete_learningconstructlevel'))
    administrators.permissions.add(Permission.objects.get(codename='add_learningconstructsublevel'))
    administrators.permissions.add(Permission.objects.get(codename='change_learningconstructsublevel'))
    administrators.permissions.add(Permission.objects.get(codename='delete_learningconstructsublevel'))
    administrators.permissions.add(Permission.objects.get(codename='add_learningconstructsublevelexample'))
    administrators.permissions.add(Permission.objects.get(codename='change_learningconstructsublevelexample'))
    administrators.permissions.add(Permission.objects.get(codename='delete_learningconstructsublevelexample'))

    # these 3 perms belong to both admins and teachers
    administrators.permissions.add(Permission.objects.get(codename='add_contexttag'))
    administrators.permissions.add(Permission.objects.get(codename='change_contexttag'))
    administrators.permissions.add(Permission.objects.get(codename='delete_contexttag'))
    teachers.permissions.add(Permission.objects.get(codename='add_contexttag'))
    teachers.permissions.add(Permission.objects.get(codename='change_contexttag'))
    teachers.permissions.add(Permission.objects.get(codename='delete_contexttag'))


class Migration(migrations.Migration):
    dependencies = [
        ('lsoa', '0022_auto_20180904_0908'),
    ]

    operations = [
        migrations.RunPython(add_permissions)
    ]
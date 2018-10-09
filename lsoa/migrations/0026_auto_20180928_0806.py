# Generated by Django 2.0.4 on 2018-09-28 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lsoa', '0025_student_student_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='status',
            field=models.CharField(choices=[('active', 'active'), ('inactive', 'inactive')], default='active', max_length=30),
        ),
        migrations.AlterField(
            model_name='contexttag',
            name='color',
            field=models.CharField(default='#17a2b8', max_length=7),
        ),
    ]

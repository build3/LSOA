# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-01-08 00:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lsoa', '0002_groups_and_perms'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='students',
            field=models.ManyToManyField(blank=True, to='lsoa.Student'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='constructs',
            field=models.ManyToManyField(blank=True, to='lsoa.LearningConstruct'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='student_groups',
            field=models.ManyToManyField(blank=True, to='lsoa.StudentGroup'),
        ),
        migrations.AlterField(
            model_name='observation',
            name='students',
            field=models.ManyToManyField(blank=True, to='lsoa.Student'),
        ),
        migrations.AlterField(
            model_name='studentgroup',
            name='students',
            field=models.ManyToManyField(blank=True, to='lsoa.Student'),
        ),
        migrations.AlterField(
            model_name='studentgrouping',
            name='groups',
            field=models.ManyToManyField(blank=True, to='lsoa.StudentGroup'),
        ),
    ]

# Generated by Django 2.0.4 on 2018-10-29 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kidviz', '0026_auto_20180928_0806'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='no_constructs',
            field=models.BooleanField(default=False),
        ),
    ]
# Generated by Django 2.0.4 on 2018-09-04 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lsoa', '0020_auto_20180809_0826'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminPerms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'permissions': (('can_approve_deny_users', 'Can Approve or Deny Users'),),
                'managed': False,
            },
        ),
    ]
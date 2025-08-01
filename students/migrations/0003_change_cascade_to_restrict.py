# Generated by Django 5.2.4 on 2025-07-30 08:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admins', '0002_change_cascade_to_restrict'),
        ('students', '0002_initial'),
        ('teachers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='attendanceclass',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, to='teachers.attendanceclass'),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='students.student'),
        ),
        migrations.AlterField(
            model_name='attendance',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='admins.subject'),
        ),
        migrations.AlterField(
            model_name='attendancetotal',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='students.student'),
        ),
        migrations.AlterField(
            model_name='attendancetotal',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='admins.subject'),
        ),
        migrations.AlterField(
            model_name='student',
            name='USN',
            field=models.CharField(max_length=100, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='student',
            name='class_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, to='admins.class'),
        ),
        migrations.AlterField(
            model_name='student',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='student',
            name='user',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='studentsubject',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='students.student'),
        ),
        migrations.AlterField(
            model_name='studentsubject',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='admins.subject'),
        ),
    ]

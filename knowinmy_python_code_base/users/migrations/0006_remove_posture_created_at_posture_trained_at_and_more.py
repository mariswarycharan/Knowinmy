# Generated by Django 4.1.1 on 2022-10-08 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_asana_is_active_posture_created_at_posture_is_active_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='posture',
            name='created_at',
        ),
        migrations.AddField(
            model_name='posture',
            name='trained_at',
            field=models.DateTimeField(null=True, verbose_name='Trained At'),
        ),
        migrations.AlterField(
            model_name='posture',
            name='last_modified_at',
            field=models.DateTimeField(null=True, verbose_name='Last Modified At'),
        ),
    ]

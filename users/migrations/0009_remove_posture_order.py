# Generated by Django 4.1.1 on 2022-10-08 15:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_rename_trained_at_posture_first_trained_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='posture',
            name='order',
        ),
    ]

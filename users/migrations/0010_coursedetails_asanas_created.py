# Generated by Django 4.1.2 on 2024-07-24 17:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_remove_enrollmentdetails_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursedetails',
            name='asanas_created',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_asanas', to='users.asana'),
        ),
    ]

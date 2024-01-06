# Generated by Django 4.1.2 on 2024-01-06 13:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0014_alter_trainer_access_model_trainer_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Student_data_model',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student_status', models.CharField(blank=True, choices=[('PENDING', 'PENDING'), ('ACCEPT', 'ACCEPT'), ('REJECT', 'REJECT')], default='PENDING', max_length=30, null=True)),
                ('trainer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.trainer_access_model')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
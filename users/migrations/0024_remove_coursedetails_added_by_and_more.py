# Generated by Django 4.1.2 on 2024-08-02 13:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0023_alter_coursedetails_course_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coursedetails',
            name='added_by',
        ),
        migrations.RemoveField(
            model_name='coursedetails',
            name='trainee_status',
        ),
        migrations.AddField(
            model_name='couponcodefornegeotiation',
            name='created_at',
            field=models.DateTimeField(null=True, verbose_name='Created at'),
        ),
        migrations.AddField(
            model_name='couponcodefornegeotiation',
            name='updated_at',
            field=models.DateTimeField(null=True, verbose_name='Last modified at'),
        ),
        migrations.AddField(
            model_name='coursedetails',
            name='asanas_by_trainer',
            field=models.ManyToManyField(related_name='asanas_created_by_trainee', to='users.asana'),
        ),
        migrations.CreateModel(
            name='TrainerLogDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(null=True, verbose_name='Created at')),
                ('updated_at', models.DateTimeField(null=True, verbose_name='Last modified at')),
                ('onboarded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='onboard_traines_by', to=settings.AUTH_USER_MODEL)),
                ('trainer_name', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='trainees', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

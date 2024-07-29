# Generated by Django 4.1.2 on 2024-07-26 13:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0011_remove_coursedetails_asanas_created'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostureAccuracy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accuracy', models.FloatField()),
                ('recorded_at', models.DateTimeField(auto_now_add=True)),
                ('asana_for_accuracy', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='postures', to='users.asana')),
                ('posture_name', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.posture')),
                ('user_to_calculate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posture_accuracies', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NumberOfAsana',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('no_of_asanas_created', models.PositiveIntegerField(blank=True, null=True)),
                ('asanas_created_by_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
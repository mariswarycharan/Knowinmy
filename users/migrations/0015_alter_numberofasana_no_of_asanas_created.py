# Generated by Django 4.1.2 on 2024-07-27 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_alter_postureaccuracy_accuracy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='numberofasana',
            name='no_of_asanas_created',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]

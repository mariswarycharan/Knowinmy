# Generated by Django 4.1.2 on 2024-07-15 17:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_subscription'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Subscription',
            new_name='Subscriptions',
        ),
    ]
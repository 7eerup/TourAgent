# Generated by Django 5.2.2 on 2025-06-13 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_user_joined_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='joined_ip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]

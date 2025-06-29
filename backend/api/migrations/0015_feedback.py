# Generated by Django 5.2.2 on 2025-06-20 06:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_alter_restaurant_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_liked', models.BooleanField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='api.chatsession')),
            ],
            options={
                'indexes': [models.Index(fields=['session', 'is_liked'], name='api_feedbac_session_5d4862_idx')],
            },
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-15 06:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflow', '0013_auto_20170804_0320'),
    ]

    operations = [
        migrations.AddField(
            model_name='tolauser',
            name='contact_info',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='tolauser',
            name='position_description',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-04 09:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Beneficiary',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('beneficiary_name', models.CharField(blank=True, max_length=255, null=True)),
                ('father_name', models.CharField(blank=True, max_length=255, null=True)),
                ('age', models.IntegerField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, max_length=255, null=True)),
                ('signature', models.BooleanField(default=True)),
                ('remarks', models.CharField(blank=True, max_length=255, null=True)),
                ('create_date', models.DateTimeField(blank=True, null=True)),
                ('edit_date', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ('beneficiary_name',),
            },
        ),
        migrations.CreateModel(
            name='BinaryField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('data', models.BinaryField()),
            ],
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distribution_name', models.CharField(max_length=255)),
                ('distribution_indicator', models.CharField(max_length=255)),
                ('distribution_implementer', models.CharField(blank=True, max_length=255, null=True)),
                ('reporting_period', models.CharField(blank=True, max_length=255, null=True)),
                ('total_beneficiaries_received_input', models.IntegerField(blank=True, null=True)),
                ('distribution_location', models.CharField(blank=True, max_length=255, null=True)),
                ('input_type_distributed', models.CharField(blank=True, max_length=255, null=True)),
                ('distributor_name_and_affiliation', models.CharField(blank=True, max_length=255, null=True)),
                ('distributor_contact_number', models.CharField(blank=True, max_length=255, null=True)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('form_filled_by', models.CharField(blank=True, max_length=255, null=True)),
                ('form_filled_by_position', models.CharField(blank=True, max_length=255, null=True)),
                ('form_filled_by_contact_num', models.CharField(blank=True, max_length=255, null=True)),
                ('form_filled_date', models.CharField(blank=True, max_length=255, null=True)),
                ('form_verified_by', models.CharField(blank=True, max_length=255, null=True)),
                ('form_verified_by_position', models.CharField(blank=True, max_length=255, null=True)),
                ('form_verified_by_contact_num', models.CharField(blank=True, max_length=255, null=True)),
                ('form_verified_date', models.CharField(blank=True, max_length=255, null=True)),
                ('total_received_input', models.CharField(blank=True, max_length=255, null=True)),
                ('total_male', models.IntegerField(blank=True, null=True)),
                ('total_female', models.IntegerField(blank=True, null=True)),
                ('total_age_0_14_male', models.IntegerField(blank=True, null=True)),
                ('total_age_0_14_female', models.IntegerField(blank=True, null=True)),
                ('total_age_15_24_male', models.IntegerField(blank=True, null=True)),
                ('total_age_15_24_female', models.IntegerField(blank=True, null=True)),
                ('total_age_25_59_male', models.IntegerField(blank=True, null=True)),
                ('total_age_25_59_female', models.IntegerField(blank=True, null=True)),
                ('create_date', models.DateTimeField(blank=True, null=True)),
                ('edit_date', models.DateTimeField(blank=True, null=True)),
                ('initiation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.WorkflowLevel2', verbose_name='Project Initiation')),
                ('office_code', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.Office')),
                ('province', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.Province')),
                ('workflowlevel1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.WorkflowLevel1')),
            ],
            options={
                'ordering': ('distribution_name',),
            },
        ),
        migrations.CreateModel(
            name='TrainingAttendance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('training_name', models.CharField(max_length=255)),
                ('implementer', models.CharField(blank=True, max_length=255, null=True)),
                ('reporting_period', models.CharField(blank=True, max_length=255, null=True)),
                ('total_participants', models.IntegerField(blank=True, null=True)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('community', models.CharField(blank=True, max_length=255, null=True)),
                ('training_duration', models.CharField(blank=True, max_length=255, null=True)),
                ('start_date', models.CharField(blank=True, max_length=255, null=True)),
                ('end_date', models.CharField(blank=True, max_length=255, null=True)),
                ('trainer_name', models.CharField(blank=True, max_length=255, null=True)),
                ('trainer_contact_num', models.CharField(blank=True, max_length=255, null=True)),
                ('form_filled_by', models.CharField(blank=True, max_length=255, null=True)),
                ('form_filled_by_contact_num', models.CharField(blank=True, max_length=255, null=True)),
                ('total_male', models.IntegerField(blank=True, null=True)),
                ('total_female', models.IntegerField(blank=True, null=True)),
                ('total_age_0_14_male', models.IntegerField(blank=True, null=True)),
                ('total_age_0_14_female', models.IntegerField(blank=True, null=True)),
                ('total_age_15_24_male', models.IntegerField(blank=True, null=True)),
                ('total_age_15_24_female', models.IntegerField(blank=True, null=True)),
                ('total_age_25_59_male', models.IntegerField(blank=True, null=True)),
                ('total_age_25_59_female', models.IntegerField(blank=True, null=True)),
                ('create_date', models.DateTimeField(blank=True, null=True)),
                ('edit_date', models.DateTimeField(blank=True, null=True)),
                ('workflowlevel1', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.WorkflowLevel1')),
                ('workflowlevel2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.WorkflowLevel2', verbose_name='Project Initiation')),
            ],
            options={
                'ordering': ('training_name',),
            },
        ),
        migrations.AddField(
            model_name='beneficiary',
            name='distribution',
            field=models.ManyToManyField(blank=True, to='formlibrary.Distribution'),
        ),
        migrations.AddField(
            model_name='beneficiary',
            name='site',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow.SiteProfile'),
        ),
        migrations.AddField(
            model_name='beneficiary',
            name='training',
            field=models.ManyToManyField(blank=True, to='formlibrary.TrainingAttendance'),
        ),
        migrations.AddField(
            model_name='beneficiary',
            name='workflowlevel1',
            field=models.ManyToManyField(blank=True, to='workflow.WorkflowLevel1'),
        ),
    ]

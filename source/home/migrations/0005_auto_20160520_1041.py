# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-20 10:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_homepagefeaturepanel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homepagefeaturepanel',
            name='glyphicon_class',
            field=models.CharField(max_length=50),
        ),
    ]

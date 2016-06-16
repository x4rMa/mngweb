# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-16 08:41
from __future__ import unicode_literals

from django.db import migrations, models
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0023_auto_20160612_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='formpage',
            name='side_panel_content',
            field=wagtail.wagtailcore.fields.RichTextField(blank=True),
        ),
        migrations.AddField(
            model_name='formpage',
            name='side_panel_title',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]

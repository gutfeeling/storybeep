# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-14 19:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20170314_1858'),
    ]

    operations = [
        migrations.AddField(
            model_name='verifiedpublisher',
            name='language',
            field=models.CharField(default='en-us', max_length=10),
            preserve_default=False,
        ),
    ]

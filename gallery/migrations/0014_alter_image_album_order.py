# Generated by Django 4.0.4 on 2022-05-20 06:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0013_category_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='album_order',
            field=models.IntegerField(help_text='Controls ordering of image within albums, and next/prev links.', unique=True),
        ),
    ]
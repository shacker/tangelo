# Generated by Django 4.0.4 on 2022-05-27 16:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_alter_album_options_image_image_api_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='image',
            name='description',
        ),
    ]

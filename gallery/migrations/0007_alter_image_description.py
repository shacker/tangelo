# Generated by Django 4.0.4 on 2022-05-13 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0006_alter_category_options_image_description_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='description',
            field=models.TextField(blank=True, help_text='Description auto-copied from Flickr description, can be overridden'),
        ),
    ]
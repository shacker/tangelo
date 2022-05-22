# Generated by Django 4.0.4 on 2022-05-22 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='simplepage',
            name='slug',
            field=models.CharField(default=1, help_text='Manually slugified version of the title', max_length=120),
            preserve_default=False,
        ),
    ]
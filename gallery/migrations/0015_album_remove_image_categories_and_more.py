# Generated by Django 4.0.4 on 2022-05-20 06:30

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0014_alter_image_album_order'),
    ]

    operations = [
        migrations.CreateModel(
            name='Album',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('title', models.CharField(help_text='Descriptive name for this album.', max_length=120, unique=True)),
                ('slug', models.CharField(help_text='Slugified version of this album title for use in URLs.', max_length=16, unique=True)),
                ('about', models.TextField(blank=True, help_text='Optional additional information this album')),
                ('order', models.IntegerField(blank=True, help_text='Controls ordering of album thumbnails on homepage', null=True)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='image',
            name='categories',
        ),
        migrations.AlterField(
            model_name='image',
            name='album_order',
            field=models.IntegerField(blank=True, help_text='Controls ordering of image within albums, and next/prev links.', unique=True),
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.AddField(
            model_name='album',
            name='cat_thumb',
            field=models.ForeignKey(blank=True, help_text='Each album should be associated with one of the images in that album, to be used in web layouts.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='gallery.image', verbose_name='Album Thumbnail'),
        ),
    ]
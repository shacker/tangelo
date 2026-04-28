from django.db import migrations


def copy_album_to_albums(apps, schema_editor):
    Image = apps.get_model("gallery", "Image")
    for image in Image.objects.select_related("album").all():
        if image.album_id:
            image.albums.add(image.album)


class Migration(migrations.Migration):

    dependencies = [
        ("gallery", "0006_image_albums"),
    ]

    operations = [
        migrations.RunPython(copy_album_to_albums, migrations.RunPython.noop),
    ]

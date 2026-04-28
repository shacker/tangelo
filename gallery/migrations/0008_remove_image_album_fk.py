from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gallery", "0007_copy_album_fk_to_m2m"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="image",
            name="album",
        ),
    ]

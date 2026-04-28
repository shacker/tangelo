from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gallery", "0005_remove_image_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="image",
            name="albums",
            field=models.ManyToManyField(
                blank=True, related_name="images", to="gallery.album"
            ),
        ),
    ]

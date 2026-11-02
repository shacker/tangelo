# Replaces the free-text Frame.aspect with a link to a standard AspectRatio.
# Each existing value snaps to the nearest standard ratio; when that changes the
# text (a different ratio, or a dropped "vertical"), the original goes to Notes.

import math
import re

import django.core.validators
import django.db.models.deletion
import django_extensions.db.fields
from django.db import migrations, models

RATIOS = [  # name, long/short, tag color
    ("1:1", "1.000", "#c9daf8"),
    ("5:4", "1.250", "#b7e1cd"),
    ("4:3", "1.333", "#fce8b2"),
    ("7:5", "1.400", "#ffd8a8"),
    ("3:2", "1.500", "#d9d2e9"),
    ("16:10", "1.600", "#f6d5e8"),
    ("5:3", "1.667", "#d0e8f2"),
    ("16:9", "1.778", "#f4c7c3"),
    ("2:1", "2.000", "#cfd8dc"),
]
ASPECT_TEXT = re.compile(r"(\d+(?:\.\d+)?)\s*[:x×/]\s*(\d+(?:\.\d+)?)")


def parse_aspect(text):
    m = ASPECT_TEXT.search(text or "")
    if not m:
        return None
    a, b = float(m.group(1)), float(m.group(2))
    if not a or not b:
        return None
    return max(a, b) / min(a, b)


def convert_aspects(apps, schema_editor):
    AspectRatio = apps.get_model("gallery", "AspectRatio")
    Frame = apps.get_model("gallery", "Frame")
    ratios = [
        AspectRatio.objects.get_or_create(name=n, defaults={"ratio": r, "color": c})[0]
        for n, r, c in RATIOS
    ]
    for frame in Frame.objects.exclude(aspect=""):
        original = frame.aspect.strip()
        value = parse_aspect(original)
        if value is not None:
            best = min(ratios, key=lambda r: abs(math.log(value / float(r.ratio))))
            frame.aspect_ratio = best
            changed = best.name != original
        else:
            changed = True  # unreadable; keep the text in Notes
        if changed:
            frame.notes = f"{frame.notes.strip()}\n\nOriginal aspect: {original}".strip()
        frame.save(update_fields=["aspect_ratio", "notes"])


def restore_aspect_text(apps, schema_editor):
    """Reverse: put the ratio name back as text (notes are left as they are)."""
    Frame = apps.get_model("gallery", "Frame")
    for frame in Frame.objects.exclude(aspect_ratio=None).select_related("aspect_ratio"):
        frame.aspect = frame.aspect_ratio.name
        frame.save(update_fields=["aspect"])


class Migration(migrations.Migration):

    dependencies = [
        ("gallery", "0009_frame_inventory"),
    ]

    operations = [
        migrations.CreateModel(
            name="AspectRatio",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name="modified"
                    ),
                ),
                ("name", models.CharField(help_text='e.g. "3:2".', max_length=20, unique=True)),
                (
                    "ratio",
                    models.DecimalField(
                        decimal_places=3,
                        help_text="Long side / short side, e.g. 1.5 for 3:2.",
                        max_digits=6,
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        default="#e8eaed",
                        help_text="Tag color in the frames grid.",
                        max_length=7,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^#[0-9a-fA-F]{6}$", "Use a hex color like #b7e1cd."
                            )
                        ],
                    ),
                ),
            ],
            options={"verbose_name": "aspect ratio", "ordering": ["ratio"]},
        ),
        migrations.AddField(
            model_name="frame",
            name="aspect_ratio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="gallery.aspectratio",
            ),
        ),
        migrations.RunPython(convert_aspects, restore_aspect_text),
        migrations.RemoveField(model_name="frame", name="aspect"),
        migrations.RenameField(model_name="frame", old_name="aspect_ratio", new_name="aspect"),
        migrations.AlterField(
            model_name="frame",
            name="aspect",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="frames",
                to="gallery.aspectratio",
            ),
        ),
    ]

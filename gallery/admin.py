from django import forms
from django.contrib import admin
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models
from django.utils.html import format_html
from jsoneditor.forms import JSONEditor
from gallery.models import (
    Album,
    AspectRatio,
    Frame,
    FrameState,
    FrameType,
    Image,
    Location,
    Price,
    SimplePage,
)


@admin.action(description="Flush cache for selected images")
def flush_image_cache(modeladmin, request, queryset):
    for obj in queryset:
        # Flush both the full image page cache and the album thumbnail
        obj.flush_cache()


@admin.action(description="Flush cache for selected album thumbnails")
def flush_album_thumb_cache(modeladmin, request, queryset):
    for obj in queryset:
        # Flush both the full image page cache and the album thumbnail
        key = make_template_fragment_key("album_thumb", [obj.slug])
        cache.delete(key)


class ImageAdminForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = "__all__"

    def clean_albums(self):
        albums = self.cleaned_data.get("albums")
        if not albums:
            raise forms.ValidationError("An image must belong to at least one album.")
        return albums


class ImageAdmin(admin.ModelAdmin):
    form = ImageAdminForm
    fields = ("flickr_id", "albums", "image_api_data", "title", "taken", "album_order")
    filter_horizontal = ("albums",)
    list_display = ("title", "flickr_id", "album_list", "taken", "created")
    list_filter = ("albums",)
    actions = [flush_image_cache]
    ordering = ["-created"]
    search_fields = ("title", "flickr_id")
    formfield_overrides = {models.JSONField: {"widget": JSONEditor()}}

    @admin.display(description="Albums")
    def album_list(self, obj):
        return ", ".join(obj.albums.values_list("title", flat=True))


class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "order",
    )
    actions = [flush_album_thumb_cache]
    autocomplete_fields = ("cat_thumb",)


admin.site.register(Image, ImageAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(SimplePage)


def tag_text_color(hex_color: str) -> str:
    """Dark text on light tags, white on dark ones (same rule as the frames grid)."""
    r, g, b = bytes.fromhex(hex_color.lstrip("#"))
    return "#202124" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#ffffff"


class TagColorAdmin(admin.ModelAdmin):
    """Lookup admin with a color picker for the grid tag color, editable in the list."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "color":
            kwargs["widget"] = forms.TextInput(attrs={"type": "color"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @admin.display(description="Tag")
    def tag(self, obj):
        return format_html(
            '<span style="background:{};color:{};padding:2px 10px;border-radius:10px">{}</span>',
            obj.color,
            tag_text_color(obj.color),
            obj,
        )


class PriceAdmin(TagColorAdmin):
    list_display = ("__str__", "tag", "color")
    list_editable = ("color",)
    search_fields = ("amount",)


class FrameStateAdmin(TagColorAdmin):
    list_display = ("name", "tag", "color", "order")
    list_editable = ("color", "order")
    search_fields = ("name",)


class LocationAdmin(TagColorAdmin):
    list_display = ("name", "tag", "color")
    list_editable = ("color",)
    search_fields = ("name",)


class FrameTypeAdmin(TagColorAdmin):
    list_display = ("name", "tag", "color")
    list_editable = ("color",)
    search_fields = ("name",)


class AspectRatioAdmin(TagColorAdmin):
    list_display = ("name", "tag", "color", "ratio")
    list_editable = ("color",)
    search_fields = ("name",)


class FrameAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "lr_id",
        "photo_id",
        "image",
        "price",
        "state_list",
        "location",
        "frame",
        "frame_type",
    )
    list_filter = ("states", "location", "price", "frame_type", "aspect")
    list_select_related = ("price", "location", "image", "frame_type", "aspect")
    autocomplete_fields = ("image",)
    search_fields = (
        "title",
        "lr_id",
        "photo_id",
        "image__flickr_id",
        "image__title",
        "frame",
        "notes",
        "print_order",
    )
    filter_horizontal = ("states",)
    fieldsets = (
        (None, {"fields": ("title", "lr_id", "photo_id", "image")}),
        ("Status", {"fields": ("states", "location", "price")}),
        (
            "Frame & image",
            {
                "fields": (
                    "frame",
                    "frame_type",
                    "image_dimension",
                    "rabbet_size",
                    ("aspect", "aspect_manual"),
                )
            },
        ),
        ("Orders & cost", {"fields": ("print_order", "print_cost")}),
        ("Notes", {"fields": ("notes",)}),
    )

    def save_model(self, request, obj, form, change):
        # Choosing an aspect by hand locks it; clearing it goes back to automatic.
        if "aspect" in form.changed_data:
            obj.aspect_manual = obj.aspect is not None
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("states")

    @admin.display(description="States")
    def state_list(self, obj):
        return ", ".join(s.name for s in obj.states.all())


admin.site.register(Price, PriceAdmin)
admin.site.register(FrameState, FrameStateAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(FrameType, FrameTypeAdmin)
admin.site.register(AspectRatio, AspectRatioAdmin)
admin.site.register(Frame, FrameAdmin)

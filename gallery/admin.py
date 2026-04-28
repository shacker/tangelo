from django import forms
from django.contrib import admin
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models
from jsoneditor.forms import JSONEditor
from gallery.models import Album, Image, SimplePage


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
    autocomplete_fields = ('cat_thumb',)


admin.site.register(Image, ImageAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(SimplePage)

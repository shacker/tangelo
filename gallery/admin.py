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


class ImageAdmin(admin.ModelAdmin):
    fields = ("flickr_id", "album", "image_api_data", "title", "taken", "album_order")
    list_display = ("title", "flickr_id", "album", "taken")
    list_filter = ("album",)
    actions = [flush_image_cache]
    ordering = ["-taken",]
    search_fields = ("title", "flickr_id")
    formfield_overrides = {models.JSONField: {"widget": JSONEditor()}}


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

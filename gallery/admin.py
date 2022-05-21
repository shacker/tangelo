from django.contrib import admin

from gallery.models import Album, Image, SimplePage

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from adminsortable2.admin import SortableAdminMixin


@admin.action(description="Flush cache for selected images")
def flush_image_cache(modeladmin, request, queryset):
    for obj in queryset:
        # Flush both the full image page cache and the album thumbnail
        key = make_template_fragment_key("flickr_full", [obj.flickr_id])
        cache.delete(key)
        key = make_template_fragment_key("flickr_thumb", [obj.flickr_id])
        cache.delete(key)


@admin.action(description="Flush cache for selected album thumbnails")
def flush_album_thumb_cache(modeladmin, request, queryset):
    for obj in queryset:
        # Flush both the full image page cache and the album thumbnail
        key = make_template_fragment_key("album_thumb", [obj.slug])
        cache.delete(key)


class ImageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ("title", "flickr_id", "album", "album_order")
    list_filter = ("album",)
    actions = [flush_image_cache]
    ordering = ["album_order"]


class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "order",
    )
    actions = [flush_album_thumb_cache]


admin.site.register(Image, ImageAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(SimplePage)

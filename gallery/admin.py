from django.contrib import admin

from gallery.models import Album, Image


class ImageAdmin(admin.ModelAdmin):
    list_display = ("title", "flickr_id", "album", "album_order")
    list_filter = ("album",)


class AlbumAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "order",
    )


admin.site.register(Image, ImageAdmin)
admin.site.register(Album, AlbumAdmin)

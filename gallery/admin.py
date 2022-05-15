from django.contrib import admin

from gallery.models import Category, Image

admin.site.register(Category)


class ImageAdmin(admin.ModelAdmin):
    list_display = ("title", "flickr_id", "albums", "album_order")
    list_filter = ("categories",)

    def albums(self, obj):
        return list(obj.categories.values_list("title", flat=True))


admin.site.register(Image, ImageAdmin)

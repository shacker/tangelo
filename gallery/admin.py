from django.contrib import admin

from gallery.models import Category, Image



class ImageAdmin(admin.ModelAdmin):
    list_display = ("title", "flickr_id", "albums", "album_order")
    list_filter = ("categories",)
    filter_horizontal = ("categories",)

    def albums(self, obj):
        return list(obj.categories.values_list("title", flat=True))

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "order",)

admin.site.register(Image, ImageAdmin)
admin.site.register(Category, CategoryAdmin)

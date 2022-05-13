from django.contrib import admin

from gallery.models import Category, Image

admin.site.register(Category)


class ImageAdmin(admin.ModelAdmin):
    list_display = ("title", "flickr_id")


admin.site.register(Image, ImageAdmin)

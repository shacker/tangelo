from django.contrib import admin

from gallery.models import Category, Image

admin.site.register(Category)


class ImageAdmin(admin.ModelAdmin):
    list_display = ("flickr_id", "title")


admin.site.register(Image, ImageAdmin)
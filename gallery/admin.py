from django.contrib import admin

from gallery.models import CategoryPage, ImagePage

admin.site.register(CategoryPage)


class ImagePageAdmin(admin.ModelAdmin):
    list_display = ("flickr_id", "title")


admin.site.register(ImagePage, ImagePageAdmin)
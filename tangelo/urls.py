from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from gallery import views

urlpatterns = [
    path("tadmin/", admin.site.urls),
    path("clear_cache", view=views.clear_cache, name="clear_cache"),
    path("about", view=views.about, name="about"),
    path("<str:album_slug>/<int:flickr_id>", view=views.image, name="image"),
    path("<str:slug>", view=views.album, name="album"),
    path("", view=views.home, name="home"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

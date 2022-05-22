from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from gallery import views

urlpatterns = [
    path("tadmin/", admin.site.urls),
    path("p/<str:page_slug>", view=views.simple_page, name="page"),
    path("<str:album_slug>/<int:flickr_id>", view=views.image, name="image"),
    path("<str:slug>", view=views.album, name="album"),
    path("", view=views.home, name="home"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

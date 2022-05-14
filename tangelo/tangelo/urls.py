from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from gallery import views

urlpatterns = [
    path("tadmin/", admin.site.urls),
    path("<str:slug>", view=views.category, name="category"),
    path("image/<int:flickr_id>", view=views.image, name="image"),
    path("", view=views.home, name="home"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

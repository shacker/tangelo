from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from gallery import views, views_frames

urlpatterns = [
    path("tadmin/", admin.site.urls),
    path("p/<str:page_slug>", view=views.simple_page, name="page"),
    path("i/<int:flickr_id>", view=views.image, name="image"),
    path("flush_cache/<int:flickr_id>", view=views.flush_cache, name="flush_cache"),
    path("refetch/<int:flickr_id>", view=views.refetch, name="refetch"),
    path("a/<str:slug>", view=views.album, name="album"),
    path("add/", view=views.add_image, name="add_image"),
    path("frames/", view=views_frames.frames_grid, name="frames_grid"),
    path("frames/add/", view=views_frames.frame_add, name="frame_add"),
    path("frames/<int:pk>/update/", view=views_frames.frame_update, name="frame_update"),
    path("frames/images/", view=views_frames.frame_image_search, name="frame_image_search"),
    path("contact/", view=views.contact, name="contact"),
    path("contact/success/", view=views.contact_success, name="contact_success"),
    path("", view=views.home, name="home"),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += staticfiles_urlpatterns()

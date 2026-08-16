from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("download/", views.start_download, name="download"),
    path("progress/<uuid:download_id>/", views.progress, name="progress"),
    path("file/<uuid:download_id>/", views.download_file, name="download_file"),
]

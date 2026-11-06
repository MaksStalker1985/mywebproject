from django.urls import path

from . import views

app_name = "forum"

urlpatterns = [
    path("", views.index, name="index"),
    path("c/<slug:slug>/", views.category, name="category"),
    path("c/<slug:slug>/new/", views.topic_create, name="topic_create"),
    path("t/<int:pk>/", views.topic_detail, name="topic"),
    path("post/<int:pk>/delete/", views.post_delete, name="post_delete"),
]

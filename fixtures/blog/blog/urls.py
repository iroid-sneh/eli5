from django.urls import path

from . import views

urlpatterns = [
    path("posts/", views.post_list),
    path("search/", views.search),
    path("admin/posts/<int:pk>/delete/", views.admin_delete_post),
    path("posts/new/", views.create_post),
    path("newsletter/", views.newsletter_signup),
]

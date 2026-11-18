from django.urls import path

from .views import (
    BoardDetailView,
    BoardListView,
    PostDetailView,
    TagDetailView,
    TagListView,
    ThreadDetailView,
    ThreadListView,
    ThreadPostListView,
)

urlpatterns = [
    path("boards/", BoardListView.as_view(), name="board-list"),
    path("boards/<slug:slug>/", BoardDetailView.as_view(), name="board-detail"),
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("tags/<slug:slug>/", TagDetailView.as_view(), name="tag-detail"),
    path("threads/", ThreadListView.as_view(), name="thread-list"),
    path("threads/<int:pk>/", ThreadDetailView.as_view(), name="thread-detail"),
    path(
        "threads/<int:pk>/posts/",
        ThreadPostListView.as_view(),
        name="thread-post-list",
    ),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
]

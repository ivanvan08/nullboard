from django.urls import path

from .views import (
    BoardDetailView,
    BoardListView,
    TagDetailView,
    TagListView,
    ThreadDetailView,
    ThreadListView,
)

urlpatterns = [
    path("boards/", BoardListView.as_view(), name="board-list"),
    path("boards/<slug:slug>/", BoardDetailView.as_view(), name="board-detail"),
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("tags/<slug:slug>/", TagDetailView.as_view(), name="tag-detail"),
    path("threads/", ThreadListView.as_view(), name="thread-list"),
    path("threads/<int:pk>/", ThreadDetailView.as_view(), name="thread-detail"),
]

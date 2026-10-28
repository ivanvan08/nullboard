from django.urls import path

from .views import BoardDetailView, BoardListView, TagDetailView, TagListView

urlpatterns = [
    path("boards/", BoardListView.as_view(), name="board-list"),
    path("boards/<slug:slug>/", BoardDetailView.as_view(), name="board-detail"),
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("tags/<slug:slug>/", TagDetailView.as_view(), name="tag-detail"),
]

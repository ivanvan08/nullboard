from django.urls import path

from .views import BoardDetailView, BoardListView

urlpatterns = [
    path("boards/", BoardListView.as_view(), name="board-list"),
    path("boards/<slug:slug>/", BoardDetailView.as_view(), name="board-detail"),
]

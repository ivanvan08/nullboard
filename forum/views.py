from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import Conflict
from .models import Board
from .serializers import BoardSerializer


class BoardListView(APIView):
    def get(self, request):
        boards = Board.objects.all()
        serializer = BoardSerializer(boards, many=True)
        return Response(serializer.data)

    def post(self, request):
        slug = request.data.get("slug")
        if Board.objects.filter(slug=slug).exists():
            raise Conflict(f"Board /{slug}/ already exists. Choose another slug.")
        serializer = BoardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BoardDetailView(APIView):
    def get(self, request, slug):
        board = get_object_or_404(Board, slug=slug)
        serializer = BoardSerializer(board)
        return Response(serializer.data)

    def patch(self, request, slug):
        board = get_object_or_404(Board, slug=slug)
        serializer = BoardSerializer(board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug):
        board = get_object_or_404(Board, slug=slug)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

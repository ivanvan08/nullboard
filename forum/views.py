from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

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
            return Response(
                {"detail": f"Дошка /{slug}/ вже існує. Оберіть інший код."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = BoardSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BoardDetailView(APIView):
    def get(self, request, slug):
        board = get_object_or_404(Board, slug=slug)
        serializer = BoardSerializer(board)
        return Response(serializer.data)

    def patch(self, request, slug):
        board = get_object_or_404(Board, slug=slug)
        serializer = BoardSerializer(board, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug):
        board = get_object_or_404(Board, slug=slug)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

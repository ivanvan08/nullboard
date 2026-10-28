from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import Conflict
from .models import Board, Post, Tag, Thread
from .serializers import (
    BoardSerializer,
    PostSerializer,
    TagSerializer,
    ThreadSerializer,
)

THREAD_ORDERING_FIELDS = ["bumped_at", "created_at", "reply_count"]


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


class TagListView(APIView):
    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

    def post(self, request):
        slug = request.data.get("slug")
        if Tag.objects.filter(slug=slug).exists():
            raise Conflict(f"Tag '{slug}' already exists. Choose another slug.")
        serializer = TagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagDetailView(APIView):
    def get(self, request, slug):
        tag = get_object_or_404(Tag, slug=slug)
        serializer = TagSerializer(tag)
        return Response(serializer.data)

    def patch(self, request, slug):
        tag = get_object_or_404(Tag, slug=slug)
        serializer = TagSerializer(tag, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, slug):
        tag = get_object_or_404(Tag, slug=slug)
        thread_count = tag.threads.count()
        if thread_count:
            raise Conflict(
                f"Tag '{slug}' cannot be deleted: it is used by {thread_count} "
                "thread(s). Remove the tag from these threads first."
            )
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ThreadListView(APIView):
    def get(self, request):
        ordering = request.query_params.get("ordering", "-bumped_at")
        if ordering.lstrip("-") not in THREAD_ORDERING_FIELDS:
            allowed = ", ".join(THREAD_ORDERING_FIELDS)
            raise serializers.ValidationError(
                {"ordering": [f"Unknown ordering. Allowed fields: {allowed}."]}
            )
        threads = Thread.objects.annotate(reply_count=Count("posts")).order_by(ordering)
        serializer = ThreadSerializer(threads, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ThreadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ThreadDetailView(APIView):
    def get(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        serializer = ThreadSerializer(thread)
        return Response(serializer.data)

    def patch(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        serializer = ThreadSerializer(thread, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        thread.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ThreadPostListView(APIView):
    def get(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        posts = thread.posts.order_by("created_at")
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        if thread.is_locked:
            raise Conflict(
                f"Thread #{thread.pk} is locked. New replies are not allowed."
            )
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(thread=thread)
        thread.bumped_at = post.created_at
        thread.save(update_fields=["bumped_at"])
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def patch(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

import logging

from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import Conflict
from .models import Board, Post, Tag, Thread
from .permissions import IsAdminUserOrReadOnly, IsAuthenticatedOrReadOnly
from .schemas import ErrorResponse
from .serializers import (
    BoardSerializer,
    PostSerializer,
    TagSerializer,
    ThreadSerializer,
)

THREAD_ORDERING_FIELDS = ["bumped_at", "created_at", "reply_count"]

logger = logging.getLogger(__name__)


@extend_schema_view(
    get=extend_schema(
        tags=["boards"],
        summary="List boards",
        responses={200: BoardSerializer(many=True)},
        auth=[],
        operation_id="boards_list",
    ),
    post=extend_schema(
        tags=["boards"],
        summary="Create a board",
        description="Staff only. The slug must be unique.",
        request=BoardSerializer,
        responses={
            201: BoardSerializer,
            400: ErrorResponse,
            401: ErrorResponse,
            403: ErrorResponse,
            409: ErrorResponse,
        },
        operation_id="boards_create",
    ),
)
class BoardListView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

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
        board = serializer.save()
        logger.info("board /%s/ created by %s", board.slug, request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["boards"],
        summary="Retrieve a board",
        responses={200: BoardSerializer, 404: ErrorResponse},
        auth=[],
        operation_id="board_retrieve",
    ),
    patch=extend_schema(
        tags=["boards"],
        summary="Update a board",
        description="Staff only. The slug cannot be changed.",
        request=BoardSerializer,
        responses={
            200: BoardSerializer,
            400: ErrorResponse,
            401: ErrorResponse,
            403: ErrorResponse,
            404: ErrorResponse,
        },
        operation_id="board_partial_update",
    ),
    delete=extend_schema(
        tags=["boards"],
        summary="Delete a board",
        description="Staff only.",
        responses={204: None, 401: ErrorResponse, 403: ErrorResponse, 404: ErrorResponse},
        operation_id="board_destroy",
    ),
)
class BoardDetailView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

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
        logger.info("board /%s/ deleted by %s", board.slug, request.user)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        tags=["tags"],
        summary="List tags",
        responses={200: TagSerializer(many=True)},
        auth=[],
        operation_id="tags_list",
    ),
    post=extend_schema(
        tags=["tags"],
        summary="Create a tag",
        description="Staff only. The slug must be unique.",
        request=TagSerializer,
        responses={
            201: TagSerializer,
            400: ErrorResponse,
            401: ErrorResponse,
            403: ErrorResponse,
            409: ErrorResponse,
        },
        operation_id="tags_create",
    ),
)
class TagListView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

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
        tag = serializer.save()
        logger.info("tag #%s created by %s", tag.slug, request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["tags"],
        summary="Retrieve a tag",
        responses={200: TagSerializer, 404: ErrorResponse},
        auth=[],
        operation_id="tag_retrieve",
    ),
    patch=extend_schema(
        tags=["tags"],
        summary="Update a tag",
        description="Staff only. The slug cannot be changed.",
        request=TagSerializer,
        responses={
            200: TagSerializer,
            400: ErrorResponse,
            401: ErrorResponse,
            403: ErrorResponse,
            404: ErrorResponse,
        },
        operation_id="tag_partial_update",
    ),
    delete=extend_schema(
        tags=["tags"],
        summary="Delete a tag",
        description="Staff only. A tag still used by threads answers 409.",
        responses={
            204: None,
            401: ErrorResponse,
            403: ErrorResponse,
            404: ErrorResponse,
            409: ErrorResponse,
        },
        operation_id="tag_destroy",
    ),
)
class TagDetailView(APIView):
    permission_classes = [IsAdminUserOrReadOnly]

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
        logger.info("tag #%s deleted by %s", tag.slug, request.user)
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        tags=["threads"],
        summary="List threads",
        description=(
            "Public endpoint. `ordering` accepts bumped_at, created_at and "
            "reply_count; prefix with `-` for descending order."
        ),
        parameters=[
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=False,
                default="-bumped_at",
            )
        ],
        responses={200: ThreadSerializer(many=True), 400: ErrorResponse},
        auth=[],
    ),
    post=extend_schema(
        tags=["threads"],
        summary="Create a thread",
        description="Requires a JWT access token. `board` and `tags` are board/tag slugs.",
        request=ThreadSerializer,
        responses={201: ThreadSerializer, 400: ErrorResponse, 401: ErrorResponse},
    ),
)
class ThreadListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        ordering = request.query_params.get("ordering", "-bumped_at")
        if ordering.removeprefix("-") not in THREAD_ORDERING_FIELDS:
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
        thread = serializer.save()
        logger.info("thread #%s created in /%s/ by %s", thread.pk, thread.board.slug, request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["threads"],
        summary="Retrieve a thread",
        responses={200: ThreadSerializer, 404: ErrorResponse},
        auth=[],
    ),
    patch=extend_schema(
        tags=["threads"],
        summary="Update a thread",
        description="Requires a JWT access token. A thread cannot be moved to another board.",
        request=ThreadSerializer,
        responses={
            200: ThreadSerializer,
            400: ErrorResponse,
            401: ErrorResponse,
            404: ErrorResponse,
        },
    ),
    delete=extend_schema(
        tags=["threads"],
        summary="Delete a thread",
        description="Deletes the thread together with its posts. Requires a JWT access token.",
        responses={204: None, 401: ErrorResponse, 404: ErrorResponse},
    ),
)
class ThreadDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        logger.info("thread #%s deleted by %s", thread.pk, request.user)
        thread.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        tags=["posts"],
        summary="List replies of a thread",
        responses={200: PostSerializer(many=True), 404: ErrorResponse},
        auth=[],
    ),
    post=extend_schema(
        tags=["posts"],
        summary="Reply to a thread",
        description="Requires a JWT access token. A locked thread answers 409.",
        request=PostSerializer,
        responses={
            201: PostSerializer,
            400: ErrorResponse,
            401: ErrorResponse,
            404: ErrorResponse,
            409: ErrorResponse,
        },
    ),
)
class ThreadPostListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        logger.info("post #%s added to thread #%s by %s", post.pk, thread.pk, request.user)
        thread.bumped_at = post.created_at
        thread.save(update_fields=["bumped_at"])
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["posts"],
        summary="Retrieve a post",
        responses={200: PostSerializer, 404: ErrorResponse},
        auth=[],
        operation_id="post_retrieve",
    ),
    patch=extend_schema(
        tags=["posts"],
        summary="Update a post",
        description="Requires a JWT access token.",
        request=PostSerializer,
        responses={
            200: PostSerializer,
            400: ErrorResponse,
            401: ErrorResponse,
            404: ErrorResponse,
        },
        operation_id="post_partial_update",
    ),
    delete=extend_schema(
        tags=["posts"],
        summary="Delete a post",
        description="Requires a JWT access token.",
        responses={204: None, 401: ErrorResponse, 404: ErrorResponse},
        operation_id="post_destroy",
    ),
)
class PostDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

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
        logger.info("post #%s deleted by %s", post.pk, request.user)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

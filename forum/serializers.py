from rest_framework import serializers

from .models import Board, Post, Tag, Thread


class BoardSerializer(serializers.ModelSerializer):
    thread_count = serializers.IntegerField(source="threads.count", read_only=True)

    class Meta:
        model = Board
        fields = ["slug", "title", "description", "thread_count"]

    def validate_slug(self, value):
        if self.instance and value != self.instance.slug:
            raise serializers.ValidationError("Board slug cannot be changed.")
        return value


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["slug", "title"]

    def validate_slug(self, value):
        if self.instance and value != self.instance.slug:
            raise serializers.ValidationError("Tag slug cannot be changed.")
        return value


class ThreadSerializer(serializers.ModelSerializer):
    board = serializers.SlugRelatedField(
        slug_field="slug", queryset=Board.objects.all()
    )
    tags = serializers.SlugRelatedField(
        slug_field="slug", queryset=Tag.objects.all(), many=True, required=False
    )
    reply_count = serializers.IntegerField(source="posts.count", read_only=True)

    class Meta:
        model = Thread
        fields = [
            "id",
            "board",
            "name",
            "subject",
            "body",
            "tags",
            "is_pinned",
            "is_locked",
            "reply_count",
            "created_at",
            "bumped_at",
        ]
        read_only_fields = ["created_at", "bumped_at"]

    def validate_board(self, value):
        if self.instance and value != self.instance.board:
            raise serializers.ValidationError(
                "Thread cannot be moved to another board."
            )
        return value


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["id", "thread", "name", "body", "created_at"]
        read_only_fields = ["thread", "created_at"]

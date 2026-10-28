from rest_framework import serializers

from .models import Board, Tag


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ["slug", "title", "description"]

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

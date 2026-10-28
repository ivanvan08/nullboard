from rest_framework import serializers

from .models import Board


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ["slug", "title", "description"]

    def validate_slug(self, value):
        if self.instance and value != self.instance.slug:
            raise serializers.ValidationError("Код дошки змінити не можна.")
        return value

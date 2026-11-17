from drf_spectacular.utils import inline_serializer
from rest_framework import serializers

ErrorResponse = inline_serializer(
    name="ErrorResponse",
    fields={
        "message": serializers.CharField(),
        "fields": serializers.DictField(
            child=serializers.ListField(child=serializers.CharField()),
            required=False,
        ),
    },
)

from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        max_length=128,
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        max_length=128,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirmation",
        ]
        extra_kwargs = {
            "username": {"required": True, "max_length": 150},
            "email": {"required": True, "max_length": 254},
            "first_name": {"required": False, "allow_blank": True, "max_length": 150},
            "last_name": {"required": False, "allow_blank": True, "max_length": 150},
        }

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("This field is required.")
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirmation = attrs.get("password_confirmation")

        if password != password_confirmation:
            raise serializers.ValidationError(
                {"password_confirmation": ["Password and confirmation do not match."]}
            )

        # Apply standard Django password validation (minimum length, complexity, similarity)
        user_candidate = User(
            username=attrs.get("username"),
            email=attrs.get("email"),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        try:
            password_validation.validate_password(password, user=user_candidate)
        except serializers.ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        except Exception as e:
            messages = getattr(e, "messages", [str(e)])
            raise serializers.ValidationError({"password": messages})

        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff"]
        read_only_fields = fields

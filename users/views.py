from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from forum.schemas import ErrorResponse

from .serializers import RegisterSerializer, UserSerializer

RegisterResponse = inline_serializer(
    name="RegisterResponse",
    fields={
        "user": UserSerializer(),
        "access": serializers.CharField(),
        "refresh": serializers.CharField(),
    },
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["auth"],
        summary="Register a user",
        description=(
            "Creates a user, returns the profile together with a JWT pair. "
            "The password is validated by Django password validators."
        ),
        request=RegisterSerializer,
        responses={201: RegisterResponse, 400: ErrorResponse},
        auth=[],
        operation_id="auth_register",
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens upon registration
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["auth"],
        summary="Current user",
        description="Returns the profile of the user the access token belongs to.",
        responses={200: UserSerializer, 401: ErrorResponse},
        operation_id="auth_me",
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

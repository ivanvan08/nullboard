import logging

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

REPORTED_STATUS_CODES = {
    status.HTTP_401_UNAUTHORIZED,
    status.HTTP_403_FORBIDDEN,
    status.HTTP_409_CONFLICT,
}


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Request conflicts with the current state."


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    if request is not None and response.status_code in REPORTED_STATUS_CODES:
        logger.warning(
            "%s %s -> %s %s",
            request.method,
            request.path,
            response.status_code,
            exc.__class__.__name__,
        )

    if isinstance(exc, ValidationError):
        response.data = {"message": "Invalid input.", "fields": response.data}
    else:
        response.data = {"message": response.data["detail"]}
    return response

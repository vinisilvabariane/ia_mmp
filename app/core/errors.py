from fastapi import status


class AppError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "internal_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationAppError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_error"


class DependencyAppError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "dependency_unavailable"


class SQLGenerationError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "sql_generation_failed"


class SQLExecutionError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "sql_execution_failed"


class RouteGenerationError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "route_generation_failed"

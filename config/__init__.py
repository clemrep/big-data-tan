"""
Module de configuration partagé pour les notebooks Big Data TAN.
"""

from .env_config import (
    GARAGE_ENDPOINT,
    ACCESS_KEY,
    SECRET_KEY,
    BUCKET_NAME,
    get_s3_path,
)
from .spark_config import create_spark_session, get_base_packages

__all__ = [
    "GARAGE_ENDPOINT",
    "ACCESS_KEY",
    "SECRET_KEY",
    "BUCKET_NAME",
    "get_s3_path",
    "create_spark_session",
    "get_base_packages",
]

"""
Configuration de la session Spark.
"""

from pyspark.sql import SparkSession
from .env_config import GARAGE_ENDPOINT, ACCESS_KEY, SECRET_KEY


def get_base_packages() -> list[str]:
    """Retourne les packages de base nécessaires pour Spark + Delta + S3."""
    return [
        "org.apache.hadoop:hadoop-aws:3.3.4",
        "com.amazonaws:aws-java-sdk-bundle:1.12.262",
        "org.apache.spark:spark-hadoop-cloud_2.12:3.5.3",
        "io.delta:delta-spark_2.12:3.0.0",
    ]


def create_spark_session(
    app_name: str,
    extra_packages: list[str] | None = None,
    log_level: str = "WARN",
    shuffle_partitions: int = 10,
) -> SparkSession:
    """
    Crée une session Spark configurée pour S3/Garage et Delta Lake.

    Args:
        app_name: Nom de l'application Spark
        extra_packages: Packages additionnels (ex: Kafka)
        log_level: Niveau de log (WARN par défaut)
        shuffle_partitions: Nombre de partitions pour les shuffles

    Returns:
        SparkSession configurée
    """
    packages = get_base_packages()
    if extra_packages:
        packages.extend(extra_packages)

    spark = (
        SparkSession.builder.appName(app_name)
        .config("spark.jars.packages", ",".join(packages))
        # Delta Lake
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        # S3/Garage configuration
        .config("spark.hadoop.fs.s3a.endpoint", GARAGE_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.endpoint.region", "garage")
        .config("spark.hadoop.fs.s3a.committer.name", "filesystem")
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
        .config("spark.hadoop.fs.s3a.multiobjectdelete.enable", "false")
        # Performance
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel(log_level)
    print(f"✅ Spark Session '{app_name}' configurée")

    return spark

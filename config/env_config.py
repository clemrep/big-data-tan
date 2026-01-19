"""
Configuration des variables d'environnement.
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

GARAGE_ENDPOINT = os.getenv("GARAGE_ENDPOINT", "http://garage:3900")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "datalake")

# Validation
if not ACCESS_KEY or not SECRET_KEY:
    raise ValueError("ACCESS_KEY et SECRET_KEY doivent être définis dans le fichier .env")

print("✅ Configuration chargée depuis .env")


def get_s3_path(*parts: str) -> str:
    """
    Construit un chemin S3 à partir du bucket et des parties fournies.

    Exemple:
        get_s3_path("silver", "flights") -> "s3a://datalake/silver/flights"
    """
    return f"s3a://{BUCKET_NAME}/{'/'.join(parts)}"

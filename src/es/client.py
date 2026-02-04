import os
from pathlib import Path

from dotenv import load_dotenv
from elasticsearch import Elasticsearch


def build_es_client() -> Elasticsearch:
    project_root = Path(__file__).resolve().parents[2]

    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    es_url = os.getenv("ES_URL", "http://localhost:9200")
    api_key = os.getenv("ES_API_KEY") or None
    username = os.getenv("ES_USERNAME") or None
    password = os.getenv("ES_PASSWORD") or None

    if api_key:
        return Elasticsearch(es_url, api_key=api_key)

    if username and password:
        return Elasticsearch(es_url, basic_auth=(username, password))

    return Elasticsearch(es_url)

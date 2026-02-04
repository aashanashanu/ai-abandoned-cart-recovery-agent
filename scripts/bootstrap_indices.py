import json
import os
from pathlib import Path

from dotenv import load_dotenv
from elasticsearch import Elasticsearch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAPPINGS_DIR = PROJECT_ROOT / "mappings"

INDEX_FILES = {
    "cart_events": "cart_events.json",
    "checkout_events": "checkout_events.json",
    "payment_logs": "payment_logs.json",
    "session_metrics": "session_metrics.json",
    "recovery_history": "recovery_history.json",
    "customer_profiles": "customer_profiles.json",
}


def build_es_client() -> Elasticsearch:
    load_dotenv(PROJECT_ROOT / ".env")

    es_url = os.getenv("ES_URL", "http://localhost:9200")
    api_key = os.getenv("ES_API_KEY") or None
    username = os.getenv("ES_USERNAME") or None
    password = os.getenv("ES_PASSWORD") or None

    if api_key:
        return Elasticsearch(es_url, api_key=api_key)

    if username and password:
        return Elasticsearch(es_url, basic_auth=(username, password))

    return Elasticsearch(es_url)


def main() -> None:
    es = build_es_client()

    for index_name, filename in INDEX_FILES.items():
        mapping_path = MAPPINGS_DIR / filename
        with mapping_path.open("r", encoding="utf-8") as f:
            body = json.load(f)

        exists = es.indices.exists(index=index_name)
        if exists:
            print(f"Index already exists: {index_name}")
            continue

        es.indices.create(index=index_name, **body)
        print(f"Created index: {index_name}")


if __name__ == "__main__":
    main()

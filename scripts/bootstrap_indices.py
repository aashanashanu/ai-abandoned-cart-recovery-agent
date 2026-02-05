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

    # Serverless takes precedence
    serverless_endpoint = os.getenv("ES_SERVERLESS_ENDPOINT")
    serverless_api_key = os.getenv("ES_SERVERLESS_API_KEY")
    if serverless_endpoint and serverless_api_key:
        print(f"Connecting to Elastic Serverless at {serverless_endpoint}")
        return Elasticsearch(serverless_endpoint, api_key=serverless_api_key)

    # Fallback to self-hosted
    es_url = os.getenv("ES_URL", "http://localhost:9200")
    api_key = os.getenv("ES_API_KEY") or None
    username = os.getenv("ES_USERNAME") or None
    password = os.getenv("ES_PASSWORD") or None

    if api_key:
        print(f"Connecting to Elasticsearch at {es_url} with API key")
        return Elasticsearch(es_url, api_key=api_key)

    if username and password:
        print(f"Connecting to Elasticsearch at {es_url} with basic auth")
        return Elasticsearch(es_url, basic_auth=(username, password))

    print(f"Connecting to Elasticsearch at {es_url} (no auth)")
    return Elasticsearch(es_url)


def main() -> None:
    es = build_es_client()

    for index_name, filename in INDEX_FILES.items():
        mapping_path = MAPPINGS_DIR / filename
        with mapping_path.open("r", encoding="utf-8") as f:
            body = json.load(f)

        # Remove settings unsupported in Serverless
        if "settings" in body:
            del body["settings"]

        exists = es.indices.exists(index=index_name)
        if exists:
            print(f"Index already exists: {index_name}")
            continue

        es.indices.create(index=index_name, **body)
        print(f"Created index: {index_name}")

    print("Bootstrap complete.")


if __name__ == "__main__":
    main()

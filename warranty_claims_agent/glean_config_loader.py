"""
Glean Configuration Loader for Warranty Claims Triage Agent.
Downloads, parses, and validates the Glean agent JSON specification from Google Cloud Storage (GCS).
"""

import os
import json
import logging
from typing import Dict, Any, Tuple, Optional
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("glean_config_loader")

DEFAULT_GCS_URI = "gs://glean_agent/warranty_claims_triage_agent.json"
REQUIRED_FIELDS = ["agent_id", "name", "description", "instructions"]

# In-memory cache
_CACHED_CONFIG: Optional[Dict[str, Any]] = None


def parse_gcs_uri(uri: str) -> Tuple[str, str]:
    """
    Parses a gs://bucket_name/object_path URI into (bucket_name, object_path).

    Args:
        uri: GCS URI string (e.g., 'gs://glean_agent/warranty_claims_triage_agent.json')

    Returns:
        Tuple[str, str]: (bucket_name, object_path)
    """
    if not uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI format. Must start with 'gs://': {uri}")
    path_part = uri[5:]
    parts = path_part.split("/", 1)
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid GCS URI: '{uri}'. Expected format: gs://<bucket_name>/<object_path>")
    return parts[0], parts[1]


def validate_glean_config(config: Dict[str, Any]) -> None:
    """
    Validates that all required Glean agent specification fields are present and non-empty.

    Args:
        config: Parsed configuration dictionary.

    Raises:
        ValueError: If config is not a dict or missing any required fields.
    """
    if not isinstance(config, dict):
        raise ValueError(f"Expected parsed Glean config to be a dict, got {type(config).__name__}")

    missing = [field for field in REQUIRED_FIELDS if not config.get(field)]
    if missing:
        raise ValueError(f"Glean configuration is missing required fields: {missing}")


def load_glean_config(gcs_uri: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Loads and parses the Glean agent JSON specification from Google Cloud Storage.

    Args:
        gcs_uri: Optional GCS URI (e.g. 'gs://glean_agent/warranty_claims_triage_agent.json').
                 Defaults to GLEAN_AGENT_GCS_URI environment variable or DEFAULT_GCS_URI.
        force_refresh: If True, bypasses in-memory cache and re-downloads from GCS.

    Returns:
        Dict[str, Any]: Parsed and validated Glean agent configuration dictionary.
    """
    global _CACHED_CONFIG
    if _CACHED_CONFIG is not None and not force_refresh:
        return _CACHED_CONFIG

    target_uri = gcs_uri or os.getenv("GLEAN_AGENT_GCS_URI") or DEFAULT_GCS_URI
    bucket_name, object_path = parse_gcs_uri(target_uri)

    logger.info(f"Downloading Glean agent JSON from GCS: gs://{bucket_name}/{object_path}")

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_path)
        raw_json_str = blob.download_as_text()

        config = json.loads(raw_json_str)
        validate_glean_config(config)

        # Update local cache in data/ for offline resilience
        try:
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            if os.path.exists(cache_dir):
                cache_file = os.path.join(cache_dir, "glean_agent_cache.json")
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
        except Exception as cache_err:
            logger.warning(f"Could not write local cache: {cache_err}")

        _CACHED_CONFIG = config
        logger.info(f"Successfully loaded Glean agent config for '{config.get('name')}' (ID: {config.get('agent_id')})")
        return config

    except Exception as e:
        logger.error(f"Failed to fetch Glean agent config from GCS ({target_uri}): {e}")

        # Attempt fallback to local disk cache if GCS is temporarily unreachable
        cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "glean_agent_cache.json")
        if os.path.exists(cache_file):
            logger.warning(f"Falling back to local cached Glean agent config: {cache_file}")
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_config = json.load(f)
                    validate_glean_config(cached_config)
                    _CACHED_CONFIG = cached_config
                    return cached_config
            except Exception as read_err:
                logger.error(f"Failed to read local cache file: {read_err}")

        raise RuntimeError(f"Unable to load Glean configuration from GCS ({target_uri}): {e}") from e

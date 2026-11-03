"""
Glean Configuration Loader for Warranty Claims Triage Agent.
Downloads, parses, and validates the Glean agent specification from Google Cloud Storage (GCS),
including the Glean Agent JSON, instructions.md, spec.yaml, and skill definitions.
"""

import os
import io
import json
import zipfile
import logging
from typing import Dict, Any, Tuple, Optional
import yaml
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("glean_config_loader")

DEFAULT_GCS_URI = "gs://glean_agent_code/Warranty_claims_triage.json"
REQUIRED_FIELDS = ["agent_id", "name", "description", "instructions"]

# In-memory cache
_CACHED_CONFIG: Optional[Dict[str, Any]] = None


def parse_gcs_uri(uri: str) -> Tuple[str, str]:
    """
    Parses a gs://bucket_name/object_path URI into (bucket_name, object_path).

    Args:
        uri: GCS URI string (e.g., 'gs://glean_agent/Warranty_claims_triage.json')

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
    Loads and parses the Glean agent specification from Google Cloud Storage.
    Retrieves the agent JSON, full instructions.md, spec.yaml, and skill definitions.

    Args:
        gcs_uri: Optional GCS URI (e.g. 'gs://glean_agent/Warranty_claims_triage.json').
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

    logger.info(f"Downloading Glean agent configuration from GCS: gs://{bucket_name}/{object_path}")

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # 1. Download Glean Agent JSON
        # If object_path points to the bundle, download the json from its standard name
        json_blob_name = object_path if object_path.endswith(".json") else "Warranty_claims_triage.json"
        json_blob = bucket.blob(json_blob_name)
        if not json_blob.exists():
            # Try lowercase / standard fallback
            for candidate in ["Warranty_claims_triage.json", "warranty_claims_triage_agent.json"]:
                if bucket.blob(candidate).exists():
                    json_blob = bucket.blob(candidate)
                    break

        raw_json_str = json_blob.download_as_text()
        config = json.loads(raw_json_str)

        # 2. Download and integrate instructions.md
        instructions_text = None
        inst_blob = bucket.blob("instructions.md")
        if inst_blob.exists():
            instructions_text = inst_blob.download_as_text()

        # 3. Download and integrate spec.yaml
        spec_text = None
        spec_blob = bucket.blob("spec.yaml")
        if spec_blob.exists():
            spec_text = spec_blob.download_as_text()

        # 4. Download skills
        skills_dict = {}
        for skill_id in ["severity-scoring", "failure-pattern-clustering"]:
            skill_blob = bucket.blob(f"skills/{skill_id}/SKILL.md")
            if skill_blob.exists():
                skills_dict[skill_id] = skill_blob.download_as_text()

        # If individual files were not directly on bucket, extract from the archive blob if present
        if not instructions_text or not spec_text or not skills_dict:
            archive_candidates = [
                "warranty_claims_triage_agent_instructions.md_spec.yaml_skills",
                os.getenv("GLEAN_AGENT_FILES_URI", "").replace(f"gs://{bucket_name}/", "")
            ]
            for arch_name in archive_candidates:
                if arch_name and bucket.blob(arch_name).exists():
                    try:
                        arch_bytes = bucket.blob(arch_name).download_as_bytes()
                        z = zipfile.ZipFile(io.BytesIO(arch_bytes))
                        for member in z.namelist():
                            if member.endswith("instructions.md") and not instructions_text:
                                instructions_text = z.read(member).decode("utf-8")
                            elif member.endswith("spec.yaml") and not spec_text:
                                spec_text = z.read(member).decode("utf-8")
                            elif "severity-scoring/SKILL.md" in member and "severity-scoring" not in skills_dict:
                                skills_dict["severity-scoring"] = z.read(member).decode("utf-8")
                            elif "failure-pattern-clustering/SKILL.md" in member and "failure-pattern-clustering" not in skills_dict:
                                skills_dict["failure-pattern-clustering"] = z.read(member).decode("utf-8")
                    except Exception as arch_err:
                        logger.warning(f"Could not extract from GCS archive {arch_name}: {arch_err}")

        # Integrate extracted GCS assets into config
        if instructions_text:
            config["instructions"] = instructions_text.strip()
            config["instructions_source"] = "gcs://instructions.md"

        if spec_text:
            try:
                config["spec"] = yaml.safe_load(spec_text)
            except Exception as y_err:
                logger.warning(f"Could not parse spec.yaml: {y_err}")
                config["spec_raw"] = spec_text

        if skills_dict:
            config["skills_definitions"] = skills_dict

        validate_glean_config(config)

        # Update local cache in data/ for offline resilience
        try:
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
            if os.path.exists(cache_dir):
                cache_file = os.path.join(cache_dir, "glean_agent_cache.json")
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)

                if instructions_text:
                    with open(os.path.join(cache_dir, "instructions.md"), "w", encoding="utf-8") as f:
                        f.write(instructions_text)
                if spec_text:
                    with open(os.path.join(cache_dir, "spec.yaml"), "w", encoding="utf-8") as f:
                        f.write(spec_text)
        except Exception as cache_err:
            logger.warning(f"Could not write local cache: {cache_err}")

        _CACHED_CONFIG = config
        logger.info(f"Successfully loaded Glean agent config for '{config.get('name')}' (ID: {config.get('agent_id')}) from GCS")
        return config

    except Exception as e:
        logger.error(f"Failed to fetch Glean agent config from GCS ({target_uri}): {e}")

        # Attempt fallback to local disk cache if GCS is temporarily unreachable
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        cache_file = os.path.join(cache_dir, "glean_agent_cache.json")
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

"""Lightweight config loader — reads config.yaml once, caches in module."""

import os
import yaml

_config = None


def get_config() -> dict:
    """Return the parsed config.yaml dict. Cached after first call."""
    global _config
    if _config is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(config_path, encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def get_constant(key: str, default=None):
    """Get a value from config.yaml's 'constants' section.

    Args:
        key: The constant name (e.g. 's9a_pass_threshold').
        default: Fallback if key is missing.

    Returns:
        The constant value, or default.
    """
    cfg = get_config()
    constants = cfg.get("constants", {})
    return constants.get(key, default)

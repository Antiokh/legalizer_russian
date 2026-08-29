from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml


class ConfigError(RuntimeError):
    pass


def _is_config_root(root: Path) -> bool:
    return (
        (root / "rules" / "rules.yaml").exists()
        and (root / "profiles" / "profiles.yaml").exists()
        and (root / "core" / "source-registry.yaml").exists()
    )


def find_project_root() -> Path:
    explicit = os.getenv("LEGALIZER_ROOT")
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if _is_config_root(root):
            return root
        raise ConfigError(f"LEGALIZER_ROOT does not contain Legalizer configuration: {root}")

    candidates = [Path.cwd().resolve(), Path(__file__).resolve().parent.parent]
    for start in candidates:
        for root in (start, *start.parents):
            if _is_config_root(root):
                return root

    # Wheels install canonical YAML files as data-files under the active Python
    # environment, so CLI use does not depend on a repository checkout.
    installed_root = Path(sys.prefix) / "share" / "legalizer_russian"
    if _is_config_root(installed_root):
        return installed_root

    raise ConfigError(
        "Cannot locate Legalizer configuration. Install the package with its data files or set LEGALIZER_ROOT."
    )


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Missing configuration file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Expected a YAML mapping in {path}")
    return data


def load_rules(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = root or find_project_root()
    data = load_yaml(root / "rules" / "rules.yaml")
    rules = data.get("rules")
    if not isinstance(rules, dict):
        raise ConfigError("rules/rules.yaml must contain a 'rules' mapping")
    return rules


def load_profiles(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = root or find_project_root()
    data = load_yaml(root / "profiles" / "profiles.yaml")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise ConfigError("profiles/profiles.yaml must contain a 'profiles' mapping")
    return profiles


def load_sources(root: Path | None = None) -> dict[str, dict[str, Any]]:
    root = root or find_project_root()
    data = load_yaml(root / "core" / "source-registry.yaml")
    sources = data.get("sources")
    if not isinstance(sources, dict):
        raise ConfigError("core/source-registry.yaml must contain a 'sources' mapping")
    return sources

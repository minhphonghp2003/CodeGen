"""Configuration loading and validation."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class FeatureConfig:
    feature_name: str
    feature_name_plural: str = ""
    solution_dir: str = ""
    domain_shared_model_folder: str = "Models\\Products"
    upsert_properties: list[list[str]] = field(default_factory=list)
    dto_properties: list[list[str]] = field(default_factory=list)
    get_all_filters: list[list[str]] = field(default_factory=list)
    dry_run: bool = False

    @property
    def entity_name(self) -> str:
        return self.feature_name

    @property
    def dto_name(self) -> str:
        return self.feature_name + "Dto"

    @property
    def model_name(self) -> str:
        return self.dto_name

    @property
    def upsert_dto_name(self) -> str:
        return "Upsert" + self.feature_name + "Dto"

    @property
    def kebab_feature_route(self) -> str:
        from .helpers import to_kebab_case
        return to_kebab_case(self.feature_name_plural)

    @property
    def feature_lower(self) -> str:
        from .helpers import to_camel_case
        return to_camel_case(self.feature_name)


def load_config(config_path: str | Path) -> FeatureConfig:
    """Load feature configuration from a YAML file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)

    feature_name = data["feature_name"]
    feature_name_plural = data.get("feature_name_plural", "")
    if not feature_name_plural:
        feature_name_plural = feature_name + "s"

    return FeatureConfig(
        feature_name=feature_name,
        feature_name_plural=feature_name_plural,
        solution_dir=data.get("solution_dir", ""),
        domain_shared_model_folder=data.get("domain_shared_model_folder", "Models\\Products"),
        upsert_properties=data.get("upsert_properties", []),
        dto_properties=data.get("dto_properties", []),
        get_all_filters=data.get("get_all_filters", []),
        dry_run=data.get("dry_run", False),
    )


def resolve_solution_dir(config_path: str | Path, solution_dir: str | None = None, config_solution_dir: str = "") -> Path:
    """Resolve the solution directory. Priority: CLI arg > YAML config > default."""
    if solution_dir:
        return Path(solution_dir)
    if config_solution_dir:
        return Path(config_solution_dir).resolve()
    # Default: parent of the config file's parent (simulating T4's Host.TemplateFile logic)
    return Path(config_path).resolve().parent.parent

"""Template rendering engine."""

from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .config import FeatureConfig
from .helpers import (
    build_filter_call_args,
    build_filter_controller_params,
    build_filter_ctor_args,
    build_filter_ctor_params,
    build_filter_predicate,
    build_filter_service_params,
    to_camel_case,
    to_kebab_case,
    to_pascal_case,
    split_words,
)

TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _build_context(cfg: FeatureConfig) -> dict:
    """Build the Jinja2 template context from configuration."""
    return {
        # Core names
        "feature_name": cfg.feature_name,
        "feature_name_plural": cfg.feature_name_plural,
        "entity_name": cfg.entity_name,
        "dto_name": cfg.dto_name,
        "model_name": cfg.model_name,
        "upsert_dto_name": cfg.upsert_dto_name,
        "kebab_feature_route": cfg.kebab_feature_route,
        "feature_lower": cfg.feature_lower,
        "domain_shared_model_folder": cfg.domain_shared_model_folder,
        # Properties
        "upsert_properties": cfg.upsert_properties,
        "dto_properties": cfg.dto_properties,
        # Filters
        "get_all_filters": cfg.get_all_filters,
        "filter_ctor_params": build_filter_ctor_params(cfg.get_all_filters),
        "filter_controller_params": build_filter_controller_params(cfg.get_all_filters),
        "filter_service_params": build_filter_service_params(cfg.get_all_filters),
        "filter_call_args": build_filter_call_args(cfg.get_all_filters),
        "filter_ctor_args": build_filter_ctor_args(cfg.get_all_filters),
        "filter_predicate": build_filter_predicate(cfg.get_all_filters),
        # Helpers
        "to_camel_case": to_camel_case,
        "to_pascal_case": to_pascal_case,
        "to_kebab_case": to_kebab_case,
        "split_words": split_words,
    }


def _create_env() -> Environment:
    """Create the Jinja2 environment."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=False,
        lstrip_blocks=False,
    )
    # Register custom filters
    env.filters["to_camel_case"] = to_camel_case
    env.filters["to_pascal_case"] = to_pascal_case
    env.filters["to_kebab_case"] = to_kebab_case
    env.filters["split_words"] = split_words
    return env


# ---------------------------------------------------------------------------
# Target definitions: (relative_path_from_solution, template_name)
# ---------------------------------------------------------------------------

TARGETS: list[tuple[str, str]] = [
    # Domain.Shared
    (
        "TMT.MyERP6.Domain.Shared/{domain_shared_model_folder}/{entity_name}.cs",
        "domain_shared/entity.cs.j2",
    ),
    (
        "TMT.MyERP6.Domain.Shared/Events/{feature_name_plural}/{feature_name}CreatedEventData.cs",
        "domain_shared/event_created.cs.j2",
    ),
    (
        "TMT.MyERP6.Domain.Shared/Events/{feature_name_plural}/{feature_name}UpdatedEventData.cs",
        "domain_shared/event_updated.cs.j2",
    ),
    (
        "TMT.MyERP6.Domain.Shared/Events/{feature_name_plural}/{feature_name}DeletedEventData.cs",
        "domain_shared/event_deleted.cs.j2",
    ),
    # Domain
    (
        "TMT.MyErp6.Domain/{feature_name_plural}/Rules/{feature_name}BusinessRule.cs",
        "domain/business_rule.cs.j2",
    ),
    (
        "TMT.MyErp6.Domain/{feature_name_plural}/Services/I{feature_name}DomainService.cs",
        "domain/domain_service_interface.cs.j2",
    ),
    (
        "TMT.MyErp6.Domain/{feature_name_plural}/Services/{feature_name}DomainService.cs",
        "domain/domain_service.cs.j2",
    ),
    # Contracts
    (
        "TMT.MyErp6.Application.Contracts/{feature_name_plural}/Dtos/{dto_name}.cs",
        "contracts/dto.cs.j2",
    ),
    (
        "TMT.MyErp6.Application.Contracts/{feature_name_plural}/Dtos/{upsert_dto_name}.cs",
        "contracts/upsert_dto.cs.j2",
    ),
    (
        "TMT.MyErp6.Application.Contracts/{feature_name_plural}/I{feature_name}QueryService.cs",
        "contracts/query_service_interface.cs.j2",
    ),
    (
        "TMT.MyErp6.Application.Contracts/{feature_name_plural}/I{feature_name}CommandService.cs",
        "contracts/command_service_interface.cs.j2",
    ),
    (
        "TMT.MyErp6.Application.Contracts/Caching/I{feature_name}Cache.cs",
        "contracts/cache_interface.cs.j2",
    ),
    # Application
    (
        "TMT.MyErp6.Application/Features/{feature_name_plural}/Services/{feature_name}QueryService.cs",
        "application/query_service.cs.j2",
    ),
    (
        "TMT.MyErp6.Application/Features/{feature_name_plural}/Services/{feature_name}CommandService.cs",
        "application/command_service.cs.j2",
    ),
    (
        "TMT.MyErp6.Application/Features/{feature_name_plural}/Caches/{feature_name}Cache.cs",
        "application/cache.cs.j2",
    ),
    (
        "TMT.MyErp6.Application/Features/{feature_name_plural}/EventHandlers/{feature_name}CacheNotificationHandler.cs",
        "application/event_handler.cs.j2",
    ),
    (
        "TMT.MyErp6.Application/Features/{feature_name_plural}/Validators/Create{feature_name}CommandValidator.cs",
        "application/validator_create.cs.j2",
    ),
    (
        "TMT.MyErp6.Application/Features/{feature_name_plural}/Validators/Update{feature_name}CommandValidator.cs",
        "application/validator_update.cs.j2",
    ),
    (
        "TMT.MyErp6.Application/Features/{feature_name_plural}/Validators/Delete{feature_name}CommandValidator.cs",
        "application/validator_delete.cs.j2",
    ),
    # Command Use Cases
    (
        "TMT.MyErp6.CommandUseCases/{feature_name_plural}/Commands/Create{feature_name}Command.cs",
        "command_use_cases/create_command.cs.j2",
    ),
    (
        "TMT.MyErp6.CommandUseCases/{feature_name_plural}/Commands/Update{feature_name}Command.cs",
        "command_use_cases/update_command.cs.j2",
    ),
    (
        "TMT.MyErp6.CommandUseCases/{feature_name_plural}/Commands/Delete{feature_name}Command.cs",
        "command_use_cases/delete_command.cs.j2",
    ),
    (
        "TMT.MyErp6.CommandUseCases/{feature_name_plural}/{feature_name}CommandHandler.cs",
        "command_use_cases/command_handler.cs.j2",
    ),
    # Query Use Cases
    (
        "TMT.MyErp6.QueryUseCases/{feature_name_plural}/Queries/GetAll{feature_name}Query.cs",
        "query_use_cases/get_all_query.cs.j2",
    ),
    (
        "TMT.MyErp6.QueryUseCases/{feature_name_plural}/Queries/GetById{feature_name}Query.cs",
        "query_use_cases/get_by_id_query.cs.j2",
    ),
    (
        "TMT.MyErp6.QueryUseCases/{feature_name_plural}/{feature_name}QueryHandler.cs",
        "query_use_cases/query_handler.cs.j2",
    ),
    # Data
    (
        "TMT.MyERP6.Data/Mappings/{feature_name}Map.cs",
        "data/mapping.cs.j2",
    ),
    # API
    (
        "TMT.MyERP6.HttpApi.Public.Host/PublicControllers/{feature_name}Controller.cs",
        "api/controller.cs.j2",
    ),
]


def _format_path(template: str, ctx: dict) -> str:
    """Expand {placeholders} in a path string."""
    result = template
    for key, value in ctx.items():
        if isinstance(value, str):
            result = result.replace("{" + key + "}", value)
    return result


def generate_files(
    cfg: FeatureConfig,
    solution_dir: str | Path,
    dry_run: bool | None = None,
) -> list[str]:
    """
    Render all templates and write output files.

    Returns a list of status messages.
    """
    if dry_run is None:
        dry_run = cfg.dry_run

    solution = Path(solution_dir)
    ctx = _build_context(cfg)
    env = _create_env()

    results: list[str] = []

    for rel_path_tpl, template_name in TARGETS:
        rel_path = _format_path(rel_path_tpl, ctx)
        full_path = solution / rel_path

        template = env.get_template(template_name)
        content = template.render(ctx)

        if dry_run:
            results.append(f"WOULD CREATE: {rel_path}")
            continue

        full_path.parent.mkdir(parents=True, exist_ok=True)

        if full_path.exists():
            results.append(f"SKIPPED (exists): {rel_path}")
            continue

        full_path.write_text(content, encoding="utf-8")
        results.append(f"CREATED: {rel_path}")

    return results


def generate_di_checklist(cfg: FeatureConfig) -> str:
    """Return the DI registration checklist string."""
    fn = cfg.feature_name
    return (
        f"  - Application: AddScoped<I{fn}QueryService, {fn}QueryService>();\n"
        f"  - Application: AddScoped<I{fn}CommandService, {fn}CommandService>();\n"
        f"  - Application: AddTransient<I{fn}DomainService, {fn}DomainService>();\n"
        f"  - Application cache: AddScoped<I{fn}Cache, {fn}Cache>();"
    )

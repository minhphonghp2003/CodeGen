"""CLI entry point for the code generator."""

from __future__ import annotations

from pathlib import Path

import click

from .config import load_config, resolve_solution_dir
from .generator import generate_di_checklist, generate_files
from .endpoint import load_endpoint_config, generate_endpoint, generate_di_checklist as generate_endpoint_di_checklist


@click.group()
def cli() -> None:
    """CQRS feature & endpoint scaffold generator."""
    pass


@cli.command("feature")
@click.argument("config_path", type=click.Path(exists=True))
@click.option(
    "-s",
    "--solution-dir",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Override the solution root directory.",
)
@click.option("--dry-run", is_flag=True, default=None, help="Preview files without writing.")
def feature_cmd(
    config_path: str,
    solution_dir: str | None,
    dry_run: bool | None,
) -> None:
    """Generate a CQRS feature scaffold from a YAML config.

    \b
    Example:
      codegen feature config/example.yaml
      codegen feature config/example.yaml -s C:\\MySolution
      codegen feature config/example.yaml --dry-run
    """
    cfg = load_config(config_path)
    sol = resolve_solution_dir(config_path, solution_dir, cfg.solution_dir)

    click.echo(f"Feature:  {cfg.feature_name}")
    click.echo(f"Solution: {sol}")
    click.echo("")

    results = generate_files(cfg, sol, dry_run=dry_run)

    for msg in results:
        click.echo(msg)

    click.echo("")
    click.echo("DI checklist:")
    click.echo(generate_di_checklist(cfg))
    click.echo("")
    click.echo("Done. Review generated code, mapping fields, validators, and DI registrations before committing.")


@cli.command("endpoint")
@click.argument("config_path", type=click.Path(exists=True))
@click.option(
    "-s",
    "--solution-dir",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Override the solution root directory.",
)
@click.option("--dry-run", is_flag=True, default=None, help="Preview files without writing.")
def endpoint_cmd(
    config_path: str,
    solution_dir: str | None,
    dry_run: bool | None,
) -> None:
    """Add a CQRS endpoint to an existing feature.

    \b
    Example:
      codegen endpoint config/endpoint_set_is_delete.yaml
      codegen endpoint config/endpoint_set_is_delete.yaml -s C:\\MySolution
      codegen endpoint config/endpoint_set_is_delete.yaml --dry-run
    """
    cfg = load_endpoint_config(config_path)
    sol = resolve_solution_dir(config_path, solution_dir, cfg.solution_dir)

    click.echo(f"Feature:   {cfg.feature_name}")
    click.echo(f"Endpoint:  {cfg.endpoint_name}")
    click.echo(f"Type:      {'Command' if cfg.is_command else 'Query'}")
    click.echo(f"Solution:  {sol}")
    click.echo("")

    results = generate_endpoint(cfg, sol, dry_run=dry_run)

    for msg in results:
        click.echo(msg)

    click.echo("")
    click.echo("DI checklist:")
    click.echo(generate_endpoint_di_checklist(cfg))
    click.echo("")
    click.echo("Done. Review generated code before committing.")


if __name__ == "__main__":
    cli()

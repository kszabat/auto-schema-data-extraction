import asyncio
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from auto_schema_data_extraction.agents.schema_agent import (
    build_schema_agent,
    generate_template_spec,
)
from auto_schema_data_extraction.config import ExtractionMode, get_settings
from auto_schema_data_extraction.extraction.pipeline import run_extraction
from auto_schema_data_extraction.models.factory import build_model
from auto_schema_data_extraction.schema.meta_models import TemplateSpec
from auto_schema_data_extraction.schema.store import (
    TemplateAlreadyExistsError,
    TemplateStoreError,
    delete_template,
    list_templates,
    load_template,
    save_template,
)

app = typer.Typer(help="Data extraction from documents via LLMs", no_args_is_help=True)
template_app = typer.Typer(help="Template management commands", no_args_is_help=True)
app.add_typer(template_app, name="template")

console = Console()


def _print_template_spec(spec: TemplateSpec) -> None:
    table = Table(title=f"Template: {spec.name}")
    table.add_column("Field")
    table.add_column("Type")
    table.add_column("Required")
    table.add_column("Description")
    for field in spec.fields:
        table.add_row(
            field.name,
            field.type,
            "Yes" if field.required else "No",
            field.description,
        )
    console.print(table)


@template_app.command("create")
def create_template(
    prompt: Annotated[
        str,
        typer.Argument(
            help="Describe the data to be extracted, e.g. 'Extract date and net amount from the invoice.'"
        ),
    ],
) -> None:
    """
    Create a new template based on the provided prompt.
    """
    asyncio.run(_template_create(prompt))


async def _template_create(prompt: str) -> None:
    settings = get_settings()
    agent = build_schema_agent(build_model(settings.schema_model))

    result = await generate_template_spec(prompt, agent=agent)

    while True:
        _print_template_spec(result.output)
        feedback = typer.prompt(
            text="Press Enter to accept, or type your feedback for changes (or 'cancel' to abort):",
            default="",
        )
        if feedback.strip().lower() == "cancel":
            console.print("[red]Template creation cancelled.[/red]")
            return
        elif feedback.strip() == "":
            break
        else:
            result = await generate_template_spec(
                feedback, agent=agent, message_history=result.all_messages()
            )

    spec = result.output

    try:
        path = save_template(spec, settings.templates_dir)
    except TemplateAlreadyExistsError:
        if typer.confirm(
            f"A template named '{spec.name}' already exists. Do you want to overwrite it?",
            default=False,
        ):
            path = save_template(spec, settings.templates_dir, overwrite=True)
        else:
            console.print("[red]Template creation aborted.[/red]")
            raise typer.Exit(code=0)

    print(f"[green]Template '{spec.name}' saved to {path}[/green]")


@template_app.command("list")
def template_list() -> None:
    """
    List all available templates.
    """
    settings = get_settings()
    names = list_templates(settings.templates_dir)
    if not names:
        console.print("[yellow]No templates found.[/yellow]")
        return
    for name in names:
        console.print(f"- {name}")


@template_app.command("show")
def template_show(
    name: Annotated[str, typer.Argument(help="Name of the template to show.")],
) -> None:
    settings = get_settings()
    try:
        spec = load_template(name, settings.templates_dir)
    except TemplateStoreError as e:
        console.print(f"[red]Error loading template '{name}': {e}[/red]")
        raise typer.Exit(code=1) from e

    _print_template_spec(spec)


@template_app.command("delete")
def template_delete(
    name: Annotated[str, typer.Argument(help="Name of the template to delete.")],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force deletion without confirmation.",
            is_flag=True,
        ),
    ] = False,
) -> None:
    settings = get_settings()
    if not force and not typer.confirm(
        f"Are you sure you want to delete the template '{name}'?", default=False
    ):
        console.print("[yellow]Deletion cancelled.[/yellow]")
        raise typer.Exit(code=0)
    try:
        delete_template(name, settings.templates_dir)
        console.print(f"[green]Template '{name}' deleted successfully.[/green]")
    except TemplateStoreError as e:
        console.print(f"[red]Error deleting template '{name}': {e}[/red]")
        raise typer.Exit(code=1) from e

    console.print(f"[green]Template '{name}' deleted successfully.[/green]")


@app.command("extract")
def extract(
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Name of the template to use for extraction.",
        ),
    ],
    files: Annotated[
        Path,
        typer.Option(
            "--files",
            "-f",
            help="Path to the document to extract data from.",
        ),
    ],
    mode: Annotated[
        ExtractionMode,
        typer.Option(
            "--mode",
            "-m",
            help="Extraction mode to use.",
        ),
    ] = None,
) -> None:
    """
    Extract data from documents using a specified template.
    """
    asyncio.run(_extract(template, files, mode))


async def _extract(template_name: str, file: Path, mode: ExtractionMode | None) -> None:
    settings = get_settings()

    try:
        spec = load_template(template_name, settings.templates_dir)
    except TemplateStoreError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc

    result = await run_extraction(
        file,
        spec,
        model_config=settings.extraction_model,
        extraction_mode=mode or settings.extraction_mode,
    )

    if result.partial:
        console.print(
            "[yellow]Document conversion was not completed successfully. This may negatively impact the accuracy of the extraction and its completeness.[/yellow]"
        )

    console.print("[green]Extraction result:[/green]")
    output_json = result.data.model_dump_json(indent=2)
    console.print(output_json)

    output_path = settings.output_dir / f"{file.stem}.json"
    output_path.write_text(data=output_json, encoding="utf-8")
    console.print(f"[green]Extraction result saved to {output_path}[/green]")


if __name__ == "__main__":
    app()

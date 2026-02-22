from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table

from .paths import list_targets
from .cleaner import CleanOptions, clean_path

app = typer.Typer(add_completion=False)
console = Console()

@app.command()
def targets():
    t = Table(title="TempCleaner targets")
    t.add_column("key")
    t.add_column("title")
    t.add_column("path")
    t.add_column("admin?")
    for tg in list_targets():
        t.add_row(tg.key, tg.title, str(tg.path), "yes" if tg.requires_admin else "no")
    console.print(t)

@app.command()
def clean(
    target: str = typer.Option("user", "--target", "-t"),
    older_days: int = typer.Option(1, "--older-days", "-d"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
    include_dirs: bool = typer.Option(True, "--dirs/--no-dirs"),
):
    tg_map = {t.key: t for t in list_targets()}
    if target not in tg_map:
        raise typer.BadParameter(f"Unknown target: {target}. Use: python -m temp_cleaner.cli targets")

    tg = tg_map[target]
    opts = CleanOptions(older_days=older_days, dry_run=dry_run, include_dirs=include_dirs)

    def log(s: str):
        console.print(s)

    stats = clean_path(tg.path, opts, log_cb=log)
    freed_mb = stats.bytes_freed / (1024 * 1024)
    console.print()
    console.print(f"[bold]Done[/bold] deleted_files={stats.deleted_files} deleted_dirs={stats.deleted_dirs} "
                  f"skipped={stats.skipped} errors={stats.errors} freed≈{freed_mb:.2f} MB")

def main():
    app()

if __name__ == "__main__":
    main()

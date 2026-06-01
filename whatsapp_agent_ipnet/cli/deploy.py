from __future__ import annotations

import os
from pathlib import Path
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


def run_deploy(
    project_id: str,
    region: str,
    service_name: str | None,
    instance_name: str | None,
    cloud_sql_instance: str | None,
    image_tag: str,
    skip_build: bool,
    skip_push: bool,
    console: Console,
) -> None:
    svc = service_name or _read_env("IPNET_INSTANCE_NAME", "whatsapp-agent")
    inst = instance_name or svc
    image = f"gcr.io/{project_id}/{svc}:{image_tag}"

    console.print(
        Panel(
            f"[bold]Deploy:[/bold] {svc}\n"
            f"[dim]Projeto:[/dim] {project_id}\n"
            f"[dim]Região:[/dim] {region}\n"
            f"[dim]Imagem:[/dim] {image}",
            title="🚀 IPNET WhatsApp Agent Deploy",
        )
    )

    _check_gcloud(console)
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        if not skip_build:
            task = progress.add_task("Buildando imagem via Cloud Build...", total=None)
            _run(["gcloud", "builds", "submit", "--tag", image, "--project", project_id], console)
            progress.update(task, description="[green]✓ Build concluído[/green]")

        task = progress.add_task("Deployando no Cloud Run...", total=None)
        deploy_cmd = [
            "gcloud",
            "run",
            "deploy",
            svc,
            "--image",
            image,
            "--region",
            region,
            "--project",
            project_id,
            "--platform",
            "managed",
            "--allow-unauthenticated",
            "--port",
            "8080",
            "--timeout",
            "300",
            "--concurrency",
            "80",
            "--min-instances",
            "0",
            "--max-instances",
            "10",
            "--set-env-vars",
            _build_env_vars(inst),
        ]
        if cloud_sql_instance:
            deploy_cmd += ["--add-cloudsql-instances", cloud_sql_instance]
        sa = _read_env("IPNET_SERVICE_ACCOUNT", "")
        if sa:
            deploy_cmd += ["--service-account", sa]
        _run(deploy_cmd, console)
        progress.update(task, description="[green]✓ Deploy concluído[/green]")

    url = _get_service_url(svc, region, project_id)
    if url:
        console.print(f"\n[green bold]✓ Agente online:[/green bold] {url}")
        console.print(f"\n[dim]Configure o webhook da Evolution API para:[/dim]")
        console.print(f"[bold]  {url}/webhook/{inst}[/bold]\n")


def _build_env_vars(instance_name: str) -> str:
    env_vars: dict[str, str] = {"IPNET_INSTANCE_NAME": instance_name}
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip().startswith("IPNET_"):
                env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return ",".join(f"{key}={value}" for key, value in env_vars.items())


def _get_service_url(service: str, region: str, project: str) -> str | None:
    try:
        result = subprocess.run(
            [
                "gcloud",
                "run",
                "services",
                "describe",
                service,
                "--region",
                region,
                "--project",
                project,
                "--format",
                "value(status.url)",
            ],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _check_gcloud(console: Console) -> None:
    try:
        subprocess.run(["gcloud", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Erro:[/red] gcloud CLI não encontrado.")
        raise SystemExit(1)


def _run(cmd: list[str], console: Console) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        console.print(f"[red]Erro:[/red]\n{result.stderr}")
        raise SystemExit(result.returncode)


def _read_env(key: str, default: str = "") -> str:
    value = os.environ.get(key, default)
    if not value:
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith(f"{key}="):
                    return line.partition("=")[2].strip().strip('"').strip("'")
    return value or default


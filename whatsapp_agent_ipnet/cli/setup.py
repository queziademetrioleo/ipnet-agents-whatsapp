from __future__ import annotations

from pathlib import Path
import re
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

_ROLES_RUNTIME = [
    ("roles/cloudsql.client", "Acesso ao Cloud SQL (OBRIGATÓRIO)"),
    ("roles/secretmanager.secretAccessor", "Leitura de secrets (OBRIGATÓRIO)"),
    ("roles/redis.editor", "Acesso ao Memorystore Redis (RECOMENDADO)"),
    ("roles/logging.logWriter", "Escrita de logs no Cloud Logging (RECOMENDADO)"),
]


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9-]", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def _sa_name(tecnico: str, projeto: str) -> str:
    tecnico_slug = _slugify(tecnico)
    projeto_slug = _slugify(projeto)
    max_body = 27
    if len(tecnico_slug) + 1 + len(projeto_slug) > max_body:
        half = (max_body - 1) // 2
        tecnico_slug = tecnico_slug[:half].rstrip("-")
        projeto_slug = projeto_slug[: max_body - 1 - len(tecnico_slug)].rstrip("-")
    slug = f"{tecnico_slug}-{projeto_slug}-sa"
    if len(slug) < 6:
        slug = slug.ljust(6, "0")
    return slug


def _run_gcloud(cmd: list[str], console: Console) -> tuple[bool, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    ok = result.returncode == 0
    output = (result.stdout + result.stderr).strip()
    if not ok:
        console.print(f"[red]Erro:[/red] {output}")
    return ok, output


def _update_env(key: str, value: str) -> None:
    env_file = Path(".env")
    if not env_file.exists():
        return
    lines = env_file.read_text().splitlines()
    found = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    env_file.write_text("\n".join(new_lines) + "\n")


def run_setup_sa(project_id: str | None, console: Console) -> None:
    console.print(
        Panel(
            "[bold]Criação de Service Account para o agente WhatsApp[/bold]\n"
            "[dim]O nome da SA será gerado automaticamente a partir do seu nome e do projeto.[/dim]",
            title="⚙️  Setup Service Account",
        )
    )

    tecnico = typer.prompt("  Seu nome (técnico responsável)", default="").strip()
    if not tecnico:
        console.print("[red]Nome do técnico não pode ser vazio.[/red]")
        raise typer.Exit(1)

    projeto = typer.prompt("  Nome do projeto / cliente").strip()
    if not projeto:
        console.print("[red]Nome do projeto não pode ser vazio.[/red]")
        raise typer.Exit(1)

    if not project_id:
        project_id = typer.prompt("  Google Cloud Project ID").strip()
    if not project_id:
        console.print("[red]Project ID não pode ser vazio.[/red]")
        raise typer.Exit(1)

    sa_name = _sa_name(tecnico, projeto)
    sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Service Account[/dim]", f"[bold]{sa_name}[/bold]")
    table.add_row("[dim]E-mail[/dim]", f"[cyan]{sa_email}[/cyan]")
    table.add_row("[dim]Projeto GCP[/dim]", project_id)
    console.print(table)
    console.print()

    typer.confirm("  Criar essa Service Account?", default=True, abort=True)

    console.print("\n[bold]1/2[/bold] Criando Service Account...")
    ok, out = _run_gcloud(
        [
            "gcloud",
            "iam",
            "service-accounts",
            "create",
            sa_name,
            "--display-name",
            f"{tecnico} - {projeto} WhatsApp Agent",
            "--project",
            project_id,
        ],
        console,
    )
    if not ok:
        if "already exists" in out:
            console.print(f"[yellow]SA '{sa_name}' já existe — prosseguindo com atribuição de roles.[/yellow]")
        else:
            raise typer.Exit(1)
    else:
        console.print(f"[green]✓[/green] SA criada: [bold]{sa_email}[/bold]")

    console.print("\n[bold]2/2[/bold] Atribuindo roles...")
    all_ok = True
    for role, descricao in _ROLES_RUNTIME:
        role_ok, _ = _run_gcloud(
            [
                "gcloud",
                "projects",
                "add-iam-policy-binding",
                project_id,
                "--member",
                f"serviceAccount:{sa_email}",
                "--role",
                role,
                "--condition",
                "None",
                "--quiet",
            ],
            console,
        )
        status = "[green]✓[/green]" if role_ok else "[red]✗[/red]"
        console.print(f"  {status} {role}  [dim]{descricao}[/dim]")
        if not role_ok:
            all_ok = False

    if Path(".env").exists():
        _update_env("IPNET_SERVICE_ACCOUNT", sa_email)
        console.print(f"\n[dim].env atualizado com IPNET_SERVICE_ACCOUNT={sa_email}[/dim]")

    console.print()
    if all_ok:
        console.print(
            Panel(
                f"[green bold]Service Account pronta![/green bold]\n\n"
                f"  SA:    [bold]{sa_name}[/bold]\n"
                f"  Email: [cyan]{sa_email}[/cyan]",
                title="✅ Pronto",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]Algumas roles não puderam ser atribuídas.[/yellow]\n"
                "Verifique se sua conta tem permissão [bold]roles/resourcemanager.projectIamAdmin[/bold].",
                title="⚠️  Atenção",
            )
        )


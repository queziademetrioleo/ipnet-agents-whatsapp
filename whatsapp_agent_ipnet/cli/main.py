from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from whatsapp_agent_ipnet.cli.deploy import run_deploy
from whatsapp_agent_ipnet.cli.setup import run_setup_sa

app = typer.Typer(
    name="whatsapp-agent",
    help="IPNET WhatsApp Agent",
    add_completion=False,
)
console = Console()


@app.command()
def deploy(
    project_id: str = typer.Option(..., "--project-id", "-p"),
    region: str = typer.Option("us-central1", "--region", "-r"),
    service_name: str = typer.Option(None, "--service", "-s"),
    instance_name: str = typer.Option(None, "--instance", "-i"),
    cloud_sql_instance: str = typer.Option(None, "--sql-instance"),
    image_tag: str = typer.Option("latest", "--tag", "-t"),
    skip_build: bool = typer.Option(False, "--skip-build"),
    skip_push: bool = typer.Option(False, "--skip-push"),
) -> None:
    run_deploy(
        project_id=project_id,
        region=region,
        service_name=service_name,
        instance_name=instance_name,
        cloud_sql_instance=cloud_sql_instance,
        image_tag=image_tag,
        skip_build=skip_build,
        skip_push=skip_push,
        console=console,
    )


@app.command(name="setup-sa")
def setup_sa(project_id: str = typer.Option(None, "--project-id", "-p")) -> None:
    run_setup_sa(project_id=project_id, console=console)


@app.command()
def qrcode(
    evolution_url: str = typer.Option(None, "--url", "-u", envvar="IPNET_EVOLUTION_API_URL"),
    api_key: str = typer.Option(None, "--key", "-k", envvar="IPNET_EVOLUTION_API_KEY"),
    instance: str = typer.Option(None, "--instance", "-i", envvar="IPNET_INSTANCE_NAME"),
) -> None:
    from whatsapp_agent_ipnet.evolution import EvolutionClient

    if not all([evolution_url, api_key, instance]):
        console.print("[red]Erro:[/red] Configure IPNET_EVOLUTION_API_URL, IPNET_EVOLUTION_API_KEY e IPNET_INSTANCE_NAME.")
        raise typer.Exit(1)

    async def _get_qr() -> None:
        client = EvolutionClient(evolution_url, api_key)
        await client.connect()
        try:
            qr = await client.get_qrcode(instance)
            if qr:
                console.print(Panel(f"[green]QR Code para instância: {instance}[/green]"))
                EvolutionClient.print_qrcode_terminal(qr)
            else:
                console.print(f"[yellow]Instância '{instance}' já está conectada ou não tem QR disponível.[/yellow]")
        finally:
            await client.disconnect()

    asyncio.run(_get_qr())


@app.command()
def status(
    evolution_url: str = typer.Option(None, "--url", envvar="IPNET_EVOLUTION_API_URL"),
    api_key: str = typer.Option(None, "--key", envvar="IPNET_EVOLUTION_API_KEY"),
    instance: str = typer.Option(None, "--instance", envvar="IPNET_INSTANCE_NAME"),
) -> None:
    from whatsapp_agent_ipnet.evolution import EvolutionClient

    if not all([evolution_url, api_key, instance]):
        console.print("[red]Erro:[/red] Variáveis de ambiente não configuradas.")
        raise typer.Exit(1)

    async def _check() -> None:
        client = EvolutionClient(evolution_url, api_key)
        await client.connect()
        try:
            state = await client.get_instance_state(instance)
            color = "green" if state.value == "open" else "yellow"
            table = Table(show_header=False, box=None)
            table.add_row("Instância", f"[bold]{instance}[/bold]")
            table.add_row("Estado", f"[{color}]{state.value.upper()}[/{color}]")
            table.add_row("URL", evolution_url)
            console.print(Panel(table, title="WhatsApp Status"))
        finally:
            await client.disconnect()

    asyncio.run(_check())


if __name__ == "__main__":
    app()

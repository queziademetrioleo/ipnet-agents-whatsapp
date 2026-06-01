#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import shutil
import sys


PLACEHOLDER_MARKERS = (
    "SUA_",
    "SEU_",
    "10.x.x.x",
    "sua-sa@",
    "https://evolution.seudominio.com",
)


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_value(key: str, file_values: dict[str, str]) -> str:
    return os.environ.get(key, file_values.get(key, ""))


def is_placeholder(value: str) -> bool:
    if not value:
        return True
    return any(marker in value for marker in PLACEHOLDER_MARKERS)


def check_command(name: str) -> tuple[bool, str]:
    return (shutil.which(name) is not None, name)


def main() -> int:
    env_path = Path(".env")
    env_values = load_env_file(env_path)

    print("IPNET WhatsApp Agent Doctor")
    print("===========================\n")

    if not env_path.exists():
        print("ERROR: .env nao encontrado. Crie com `cp .env.example .env`.")
        return 1

    required = [
        "IPNET_AGENT_NAME",
        "IPNET_INSTANCE_NAME",
        "IPNET_GEMINI_API_KEY",
        "IPNET_EVOLUTION_API_URL",
        "IPNET_EVOLUTION_API_KEY",
        "IPNET_POSTGRES_URL",
        "IPNET_REDIS_URL",
    ]

    errors: list[str] = []
    warnings: list[str] = []

    for key in required:
        value = get_value(key, env_values)
        if not value:
            errors.append(f"{key} ausente")
        elif is_placeholder(value):
            warnings.append(f"{key} ainda parece placeholder")

    service_account = get_value("IPNET_SERVICE_ACCOUNT", env_values)
    if service_account and is_placeholder(service_account):
        warnings.append("IPNET_SERVICE_ACCOUNT ainda parece placeholder")

    for command in ("python3", "docker", "gcloud"):
        ok, name = check_command(command)
        if not ok:
            warnings.append(f"comando nao encontrado no PATH: {name}")

    print("Checagens de ambiente:")
    print(f"- .env encontrado: {'sim' if env_path.exists() else 'nao'}")
    print(f"- python3 no PATH: {'sim' if shutil.which('python3') else 'nao'}")
    print(f"- docker no PATH: {'sim' if shutil.which('docker') else 'nao'}")
    print(f"- gcloud no PATH: {'sim' if shutil.which('gcloud') else 'nao'}")

    print("\nVariaveis essenciais:")
    for key in required:
        value = get_value(key, env_values)
        status = "ok"
        if not value:
            status = "missing"
        elif is_placeholder(value):
            status = "placeholder"
        print(f"- {key}: {status}")

    if service_account:
        sa_status = "placeholder" if is_placeholder(service_account) else "ok"
        print(f"- IPNET_SERVICE_ACCOUNT: {sa_status}")
    else:
        print("- IPNET_SERVICE_ACCOUNT: vazio (ok se ainda nao for deployar)")

    if errors:
        print("\nErros:")
        for error in errors:
            print(f"- {error}")

    if warnings:
        print("\nAvisos:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("\nResultado: FAIL")
        return 1

    print("\nResultado: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

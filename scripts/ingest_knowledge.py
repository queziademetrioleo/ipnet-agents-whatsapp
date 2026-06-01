from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import AppConfig
from app.knowledge.service import build_knowledge_service


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingesta arquivos de texto/markdown na base vetorial do agente."
    )
    parser.add_argument("paths", nargs="+", help="Arquivos para ingestao.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = AppConfig.from_env()
    knowledge = build_knowledge_service(config)

    if not knowledge.enabled:
        print("Base de conhecimento nao configurada. Verifique IPNET_POSTGRES_URL e IPNET_GEMINI_API_KEY.")
        return 1

    total_chunks = 0
    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"[skip] arquivo nao encontrado: {path}")
            continue
        chunks = knowledge.ingest_file(path)
        total_chunks += chunks
        print(f"[ok] {path} -> {chunks} chunk(s)")

    print(f"[done] total de chunks ingeridos: {total_chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

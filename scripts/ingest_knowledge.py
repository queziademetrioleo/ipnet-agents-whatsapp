from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import AppConfig
from app.knowledge.service import build_knowledge_service


def _load_csv_qa(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = {name.strip().lower(): name for name in (reader.fieldnames or [])}
        question_field = fieldnames.get("pergunta") or fieldnames.get("question")
        answer_field = fieldnames.get("resposta") or fieldnames.get("answer")

        if not question_field or not answer_field:
            raise ValueError(
                f"{path.name} precisa ter colunas 'pergunta' e 'resposta'. "
                f"Colunas encontradas: {reader.fieldnames or []}"
            )

        sections: list[str] = []
        for index, row in enumerate(reader, start=1):
            question = (row.get(question_field) or "").strip()
            answer = (row.get(answer_field) or "").strip()
            if not question or not answer:
                continue
            sections.append(
                f"## Pergunta {index}\n"
                f"Pergunta: {question}\n"
                f"Resposta: {answer}"
            )

    if not sections:
        raise ValueError(f"{path.name} nao possui linhas validas com pergunta e resposta.")

    return "\n\n".join(sections)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingesta arquivos de texto/markdown ou CSV pergunta-resposta na base vetorial do agente."
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
        if path.suffix.lower() == ".csv":
            content = _load_csv_qa(path)
            chunks = knowledge.ingest_text(
                title=path.stem,
                content=content,
                source_uri=str(path),
                document_id=path.stem,
            )
        else:
            chunks = knowledge.ingest_file(path)
        total_chunks += chunks
        print(f"[ok] {path} -> {chunks} chunk(s)")

    print(f"[done] total de chunks ingeridos: {total_chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from app.config import AppConfig
from app.repositories.leads import LeadRecord, LeadRepository


class LeadCaptureService:
    def __init__(self, repository: LeadRepository | None) -> None:
        self.repository = repository

    def capture_interest(
        self,
        name: str,
        email: str,
        phone: str,
        subject: str,
        notes: str = "",
    ) -> LeadRecord:
        if self.repository is None:
            raise RuntimeError("Persistencia de leads nao configurada.")
        self.repository.ensure_schema()
        return self.repository.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            notes=notes,
        )


def build_lead_capture_service(config: AppConfig) -> LeadCaptureService:
    if not config.postgres_url:
        return LeadCaptureService(repository=None)
    repository = LeadRepository(dsn=config.postgres_sync_url, schema=config.lead_schema)
    return LeadCaptureService(repository=repository)


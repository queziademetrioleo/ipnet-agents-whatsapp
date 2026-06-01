.PHONY: help infra-up infra-down setup doctor validate run health qrcode status setup-sa deploy logs ingest-knowledge

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
AGENT := $(PYTHON) -m whatsapp_agent_ipnet.cli.main

help:
	@printf "Targets disponiveis:\n"
	@printf "  make infra-up\n"
	@printf "  make infra-down\n"
	@printf "  make setup\n"
	@printf "  make doctor\n"
	@printf "  make validate\n"
	@printf "  make run\n"
	@printf "  make health\n"
	@printf "  make qrcode\n"
	@printf "  make status\n"
	@printf "  make ingest-knowledge FILES=\"docs/faq.md docs/produto.md\"\n"
	@printf "  make deploy PROJECT_ID=... REGION=... SERVICE=... SQL_INSTANCE=...\n"
	@printf "  make logs PROJECT_ID=... REGION=... SERVICE=...\n"

infra-up:
	docker compose up -d postgres redis

infra-down:
	docker compose down

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

doctor:
	python3 scripts/doctor.py

validate:
	$(PYTHON) -m compileall main.py app scripts whatsapp_agent_ipnet

run:
	$(PYTHON) main.py

health:
	curl -fsS http://127.0.0.1:8080/webhook/health

qrcode:
	$(AGENT) qrcode

status:
	$(AGENT) status

ingest-knowledge:
	test -n "$(FILES)"
	$(PYTHON) scripts/ingest_knowledge.py $(FILES)

setup-sa:
	$(AGENT) setup-sa

deploy:
	test -n "$(PROJECT_ID)"
	test -n "$(REGION)"
	test -n "$(SERVICE)"
	test -n "$(SQL_INSTANCE)"
	$(AGENT) deploy \
		--project-id "$(PROJECT_ID)" \
		--region "$(REGION)" \
		--service "$(SERVICE)" \
		--sql-instance "$(SQL_INSTANCE)"

logs:
	test -n "$(PROJECT_ID)"
	test -n "$(REGION)"
	test -n "$(SERVICE)"
	gcloud run services logs tail "$(SERVICE)" \
		--project "$(PROJECT_ID)" \
		--region "$(REGION)"

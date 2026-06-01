.PHONY: help setup run health qrcode status setup-sa deploy logs

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
AGENT := $(VENV)/bin/whatsapp-agent

help:
	@printf "Targets disponiveis:\n"
	@printf "  make setup\n"
	@printf "  make run\n"
	@printf "  make health\n"
	@printf "  make qrcode\n"
	@printf "  make status\n"
	@printf "  make deploy PROJECT_ID=... REGION=... SERVICE=... SQL_INSTANCE=...\n"
	@printf "  make logs PROJECT_ID=... REGION=... SERVICE=...\n"

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py

health:
	curl -fsS http://127.0.0.1:8080/webhook/health

qrcode:
	$(AGENT) qrcode

status:
	$(AGENT) status

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

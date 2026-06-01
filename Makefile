.PHONY: setup run qrcode status setup-sa deploy

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
AGENT := $(VENV)/bin/whatsapp-agent

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) main.py

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

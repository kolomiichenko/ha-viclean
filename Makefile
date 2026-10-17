VENV ?= .venv
PY := $(VENV)/bin/python
HA_HOST ?= andrii@192.168.0.95
HA_CONFIG ?= ~/homeassistant/config

.PHONY: venv test lint deploy

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q pytest ruff

test:
	$(PY) -m pytest -q

lint:
	$(VENV)/bin/ruff check custom_components tests

# Copies the integration to a Home Assistant host over SSH and restarts it.
deploy:
	rsync -a --delete --exclude __pycache__ custom_components/viclean/ $(HA_HOST):/tmp/viclean/
	ssh $(HA_HOST) 'sudo rsync -a --delete /tmp/viclean/ $(HA_CONFIG)/custom_components/viclean/ && docker restart homeassistant'

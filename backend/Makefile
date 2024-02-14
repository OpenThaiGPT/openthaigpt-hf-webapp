# # Virtual environment management
# params
# Python for creating the virtual environment
SYS_PY ?= python3.11

PY_VENV=venv
# Environment cli tools
PYTHON = $(PY_VENV)/bin/python
PIP = $(PY_VENV)/bin/pip
PIP_SYNC = $(PY_VENV)/bin/pip-sync
PIP_COMPILE = $(PY_VENV)/bin/pip-compile
# Enviroment variables
PROJECT_DIR = $(shell pwd)
export PYTHONPATH = $(PROJECT_DIR)

HOST=0.0.0.0
PORT=8000

export SESSION_KEY=openthaigpt-super-secret-key

run:
	$(PYTHON) -m uvicorn otgpt_hft.server:app \
		--host $(HOST) \
		--port $(PORT) \
		--log-config logging-config.json \
		--lifespan on
dev:
	$(PYTHON) -m uvicorn otgpt_hft.server:app \
		--host $(HOST) \
		--port $(PORT) \
		--log-config logging-config.json \
		--lifespan on \
		--reload-exclude .git \
		--reload
pg:
	$(PYTHON) -m pg

test:
	$(PYTHON) -m pytest

jupyter-server:
	venv/bin/jupyter lab --no-browser

# initialize and setup new virtual environment (venv)
cmd-init-env:
	$(MAKE) $(PY_VENV)
	$(PIP) install pip-tools
	$(MAKE) requirements/requirements.in
	$(MAKE) cmd-sync-env

$(PYTHON): cmd-init-env

# sync venv with dependencies specified in `requirements/*`
cmd-sync-env: requirements.txt
	$(PIP_SYNC) requirements.txt
	$(PIP) freeze

# quick and dirty install of packages
pip-install:
	$(PIP) install -r requirements.txt
	
# initialize a bare virtual environment (venv)
$(PY_VENV):
	$(SYS_PY) -m venv $(PY_VENV)

# prep requirements
requirements/requirements.in:
	mkdir -p requirements
	touch requirements/requirements.in

requirements.txt: requirements/*
	$(PIP_COMPILE) requirements/*.in -o requirements.txt

# run some script in processing dir
# Example usage
# $ make process SCRIPT=scripts/import_text.py
process:
	test ${SCRIPT} # check if $${SCRIPT} is set
	$(PYTHON) $(SCRIPT)

cp-page:
	
	cp /Users/anuruth.l/dev/learning/shadcn-ui/react-manual/dist/* ./page/
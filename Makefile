# ==============================================================================
# ScamShield Makefile — Common Developer & CI Tasks
# ==============================================================================

.PHONY: help setup run test harness clean

# Detect Python inside virtualenv (cross-platform)
ifeq ($(OS),Windows_NT)
    VENV_PYTHON = .venv\Scripts\python.exe
    VENV_PIP = .venv\Scripts\pip.exe
    VENV_UVICORN = .venv\Scripts\uvicorn.exe
else
    VENV_PYTHON = .venv/bin/python
    VENV_PIP = .venv/bin/pip
    VENV_UVICORN = .venv/bin/uvicorn
endif

help:
	@echo "ScamShield Developer Commands:"
	@echo "  make setup    - Create virtualenv and install dependencies"
	@echo "  make run      - Run backend server (http://127.0.0.1:8080)"
	@echo "  make test     - Run pytest test suites"
	@echo "  make harness  - Run safety and adversarial invariant harness"
	@echo "  make clean    - Clean temporary build and cache artifacts"

setup:
	@python -m venv .venv
	@$(VENV_PIP) install -r requirements.txt
	@if [ ! -f .env ] && [ -f .env.example ]; then cp .env.example .env; fi
	@echo "Setup complete. Virtualenv created in .venv"

run:
	@$(VENV_PYTHON) -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload

test:
	@$(VENV_PYTHON) -m pytest

harness:
	@$(VENV_PYTHON) -m harness.run

clean:
	@rm -rf __pycache__ .pytest_cache .coverage htmlcov

SHELL := /bin/bash

PYTHON = python
VENV_NAME = venv

SOURCE = source $(VENV_NAME)/bin/activate

install:
	$(PYTHON) -m venv $(VENV_NAME)
	$(SOURCE) && ./$(VENV_NAME)/bin/pip install --upgrade pip
	$(SOURCE) && ./$(VENV_NAME)/bin/pip install -r requirements.txt
	$(SOURCE) && ./$(VENV_NAME)/bin/pip install -e .
	echo Done.

clean:
	rm -rf $(VENV_NAME) "pip-wheel-metadata" "build" "dist"
	find . -depth -name "*.egg*" -exec rm -rf "{}" \;

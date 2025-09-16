PIP_REPO_URL := $(shell pip3.11 config get install.find-links 2> /dev/null)

PYTHON=python3.11
ENV_DIR=.env_$(PYTHON)
PROJECT_FOLDERS=src tests
VERBOSITY ?= 1

export PYTHONPATH=.
export DJANGO_SETTINGS_MODULE=propylon_document_manager.site.settings.local

ifeq ($(OS),Windows_NT)
	IN_ENV=. $(ENV_DIR)/Scripts/activate &&
else
	IN_ENV=. $(ENV_DIR)/bin/activate &&
endif

# ======================
# Environment management
# ======================
$(ENV_DIR):
	virtualenv -p $(PYTHON) $(ENV_DIR)
	@printf "[install]\nfind-links=$(PIP_REPO_URL)\n" > $(ENV_DIR)/pip.conf

print-install-message:
	@printf "Environment installed at $(ENV_DIR), run the following command to activate it: \nsource $(ENV_DIR)/bin/activate\n"

env: $(ENV_DIR) print-install-message

requirements: requirements/main.txt requirements/dev.txt build-reqs

env_update: $(ENV_DIR) requirements
	$(IN_ENV) pip install -U -r requirements/dev.txt

# ======================
# Testing and Linting
# ======================
test: build plain-test

plain-test:
	$(IN_ENV) py.test

# ====================
# Clean
# ====================
clean:
	- @rm -rf src/*.egg-info
	- @rm -rf build
	- @rm -rf dist
	- @rm -f .coverage
	- @rm -f test_results.xml
	- @rm -f coverage.xml
	- @find ./src -name '*.pyc' | xargs -r rm
	- @find ./ -name '__pycache__' | xargs rm -rf


env_clean: clean
	- @rm -rf $(ENV_DIR)

# ====================
# Developer Utilities
# ====================
shell:
	$(IN_ENV) django-admin shell

collectstatic:
	$(IN_ENV) django-admin collectstatic

build-reqs: env
	$(IN_ENV) pip install -r requirements/dev.txt

build: build-reqs
	$(IN_ENV) pip install -e .

plain-serve:
	$(IN_ENV) django-admin runserver 0.0.0.0:8001

serve: build makemigrations migrate plain-serve

# ============================
# Database & Fixture Utilities
# ============================
makemigrations:
	$(IN_ENV) django-admin makemigrations

migrate:
	$(IN_ENV) django-admin migrate

fixture: build makemigrations migrate plain-fixture

plain-fixture:
	$(IN_ENV) django-admin load_file_fixtures

seed-data: build makemigrations migrate plain-seed-data

plain-seed-data:
	$(IN_ENV) django-admin seed_data

create-user-with-file: build makemigrations migrate plain-create-user-with-file

plain-create-user-with-file:
	$(IN_ENV) django-admin create_user_with_file $(email) $(password) $(url)

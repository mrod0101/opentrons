# opentrons notify server makefile

include ../scripts/push.mk
include ../scripts/python.mk

SHX := npx shx

# Path of source package
SRC_PATH = notify_server

wheel_file = dist/notify_server-*-py3-none-any.whl

# These variables can be overriden when make is invoked to customize the
# behavior of pytest. For instance,
# make test tests=tests/opentrons/tools/test_qc_scripts.py would run only the
# specified test
tests ?= tests
test_opts ?= --cov=$(SRC_PATH) --cov-report term-missing:skip-covered --cov-report xml:coverage.xml

# Host key location for buildroot robot
br_ssh_key ?= $(default_ssh_key)
# Pubkey location for buildroot robot to install with install-key
br_ssh_pubkey ?= $(br_ssh_key).pub
# Other SSH args for buildroot robots
ssh_opts ?= $(default_ssh_opts)

# Source discovery
# For the python sources
ot_py_sources := $(filter %.py,$(shell $(SHX) find $(SRC_PATH)))
ot_sources := pyproject.toml $(ot_py_sources)

# Defined separately than the clean target so the wheel file doesn’t have to
# depend on a PHONY target
clean_cmd = $(SHX) rm -rf build dist .coverage coverage.xml "*.egg-info" "**/__pycache__" "**/*.pyc" "**/.mypy_cache" "**/.pytest_cache"

.PHONY: all
all: clean wheel

.PHONY: setup
setup:
	$(pipenv) sync $(pipenv_opts)
	$(pipenv) run pip freeze

.PHONY: clean
clean:
	$(clean_cmd)

.PHONY: teardown
teardown:
	$(pipenv) --rm

dist/notify_server-%-py3-none-any.whl: $(ot_sources)
	poetry build --format wheel

wheel: $(wheel_file)

.PHONY: test
test:
	$(pytest) $(tests) $(test_opts)

.PHONY: lint
lint: $(ot_py_sources)
	$(python) -m mypy $(SRC_PATH) $(tests)
	$(python) -m flake8 $(SRC_PATH) $(tests)

.PHONY: dev
dev: export OT_NOTIFY_SERVER_PRODUCTION := 0
dev:
	$(python) -m notify_server.main

.PHONY: local-shell
local-shell:
	$(python) shell

.PHONY: push
push: clean wheel
	$(call push-python-package,$(host),$(br_ssh_key),$(ssh_opts),$(wheel_file))
	$(call push-systemd-unit,$(host),$(br_ssh_key),$(ssh_opts),./opentrons-notify-server.service)
	$(call restart-service,$(host),$(br_ssh_key),$(ssh_opts),opentrons-notify-server)

.PHONY: install-key
install-key:
	curl -X POST $(host):31950/server/ssh_keys\
		-H "Content-Type: application/json"\
		-d "{\"key\":\"$(shell cat $(br_ssh_pubkey))\"}"

# User must currently specify host, e.g.: `make term host=169.254.202.176`
.PHONY: term
term:
	ssh -i $(br_ssh_key) $(ssh_opts) root@$(host)

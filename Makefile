.PHONY: help up dc stop down restart build logs bash setup init dbsetup demodata testsetup test deploy clean

# Default target
help:
	@echo "ADX Development Environment Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  up         - Start docker containers (docker-compose up -d)"
	@echo "  dc         - Run any docker-compose command (use DC_ARGS for arguments)"
	@echo "  stop       - Stop docker containers"
	@echo "  down       - Stop and destroy docker containers"
	@echo "  restart    - Restart docker containers"
	@echo "  build      - Build docker containers"
	@echo "  logs       - Open the logs for a service (use SERVICE for service name)"
	@echo "  bash       - Open a bash prompt in a container (use CONTAINER for container name)"
	@echo "  setup      - Set up the ADX codebase locally"
	@echo "  init       - Initialize ADX project (configure submodules)"
	@echo "  dbsetup    - Run initial configuration for CKAN plugins"
	@echo "  demodata   - Load demo example data to local CKAN"
	@echo "  testsetup  - Set up the database for CKAN tests"
	@echo "  test       - Test a CKAN extension (use EXT for extension name)"
	@echo "  deploy     - Deploy master branch (if deploy script exists)"
	@echo "  clean      - Clean up Python cache files"
	@echo ""
	@echo "Examples:"
	@echo "  make up"
	@echo "  make logs SERVICE=ckan"
	@echo "  make bash CONTAINER=ckan"
	@echo "  make test EXT=validation"
	@echo "  make dc DC_ARGS='ps'"

# Docker compose commands
up:
	./adx up

dc:
	./adx dc $(DC_ARGS)

stop:
	./adx stop

down:
	./adx down

restart:
	./adx restart

build:
	./adx build

logs:
	./adx logs $(SERVICE)

bash:
	./adx bash $(CONTAINER)

# Setup and initialization commands
setup:
	./adx setup

init:
	./adx init

dbsetup:
	./adx dbsetup

demodata:
	./adx demodata

testsetup:
	./adx testsetup

# Testing
test:
	./adx test $(EXT)

# Deployment (if available)
deploy:
	./adx deploy

# Utility targets
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +

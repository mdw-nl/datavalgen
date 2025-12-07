# Docker image
IMAGE_NAME ?= ghcr.io/mdw-nl/datavalgen
# Get version from pyproject.toml
PY_PKG_VERSION := $(shell python -c 'import tomllib, pathlib; d = tomllib.loads(pathlib.Path("pyproject.toml").read_text()); print(d["project"]["version"])')
GIT_TAG := release/v$(PY_PKG_VERSION)
DOCKER_TAG := v$(TAG)
DOCKERFILE ?= ./Dockerfile


# Default target
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	docker build -t $(IMAGE_NAME):$(DOCKER_TAG) -t $(IMAGE_NAME):latest -f $(DOCKERFILE) .

.PHONY: tag
tag:
	git tag "$(GIT_TAG)"

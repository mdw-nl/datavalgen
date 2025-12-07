# Docker image
IMAGE_NAME ?= ghcr.io/mdw-nl/datavalgen
TAG ?= 0.1.0
DOCKERFILE ?= ./Dockerfile

# Default target
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	docker build -t $(IMAGE_NAME):$(TAG) -t $(IMAGE_NAME):latest -f $(DOCKERFILE) .

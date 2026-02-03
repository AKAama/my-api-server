export SHELL := /bin/bash
export SHELLOPTS := errexit:pipefail

# 镜像基本信息
REGISTRY    ?= testhub.sudytech.cn
IMAGE_REPO  ?= webplus
APP_NAME    ?= my-api-server
TAG         ?= 1.0.0

IMAGE       := $(REGISTRY)/$(IMAGE_REPO)/$(APP_NAME):$(TAG)

# Docker
DOCKERFILE ?= Dockerfile
PLATFORMS  ?= linux/amd64,linux/arm64

# 默认目标
.PHONY: all
all: image-build-push

# 初始化 buildx
.PHONY: docker-buildx-init
docker-buildx-init:
	@docker buildx inspect >/dev/null 2>&1 || docker buildx create --use
	@docker buildx inspect --bootstrap >/dev/null

# 构建并推送多架构镜像
.PHONY: image-build-push
image-build-push: docker-buildx-init
	@echo "==> Building & pushing $(IMAGE)"
	docker buildx build \
		--platform $(PLATFORMS) \
		-f $(DOCKERFILE) \
		-t $(IMAGE) \
		--push .

# 本地构建（仅当前架构）
.PHONY: image-build-local
image-build-local:
	docker build \
		-f $(DOCKERFILE) \
		-t $(IMAGE) .

# 查看镜像架构
.PHONY: image-inspect
image-inspect:
	docker buildx imagetools inspect $(IMAGE)

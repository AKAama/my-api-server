FROM python:3.11-slim
LABEL authors="fanxun <xunfan@sudytech.com>"

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata ca-certificates && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip \
    && pip install . --no-build-isolation

COPY app/ ./app/
COPY main.py ./

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "main.py"]
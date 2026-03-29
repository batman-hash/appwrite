FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libcurl4-openssl-dev \
    libsqlite3-dev \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/devnavigator

COPY requirements.txt ./

RUN python -m pip install --upgrade pip && \
    grep -v '^sqlite3-python==' requirements.txt > /tmp/requirements.docker.txt && \
    pip install --no-cache-dir -r /tmp/requirements.docker.txt

COPY . .

RUN mkdir -p /workspace/database /workspace/data /workspace/logs

WORKDIR /workspace

ENTRYPOINT ["python3", "/opt/devnavigator/devnavigator.py"]
CMD ["--help"]

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
COPY models/baseline/creditscorev4.joblib ./models/baseline/creditscorev4.joblib

RUN python -m pip install --upgrade pip \
    && python -m pip install . \
    && groupadd --gid 10001 creditscore \
    && useradd \
        --uid 10001 \
        --gid 10001 \
        --no-create-home \
        --shell /usr/sbin/nologin \
        creditscore

USER 10001:10001

EXPOSE 8000

CMD ["python", "scripts/serve_model.py", "--host", "0.0.0.0", "--port", "8000"]
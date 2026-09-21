FROM python:3.12.14-slim-bookworm@sha256:d5ae74acb8026b32a2f6deea45003c5bd4e2880700c19c44bda54670ad3eff90

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md constraints.lock ./
COPY src ./src
COPY configs ./configs
COPY scripts ./scripts
COPY models/baseline/creditscorev4.joblib ./models/baseline/creditscorev4.joblib

RUN python -m pip install . -c constraints.lock \
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
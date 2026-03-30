FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.10 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

CMD ["uv", "run", "--no-sync", "python3", "server.py"]

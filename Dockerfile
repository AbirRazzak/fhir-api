FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Deps first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY app ./app
COPY resources ./resources

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "fastapi", "run", "app/main.py", "--port", "8000"]

# fhir-api
API to fetch and upload FHIR data

## Development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync                  # install deps
uv run fastapi dev       # run with reload at http://127.0.0.1:8000 (docs at /docs)
uv run pytest            # tests
uv run ruff check . && uv run ruff format .   # lint + format
```

Docker:

```sh
docker compose up --build   # hot-reloads on changes to app/
docker build -t fhir-api . && docker run -p 8000:8000 fhir-api   # prod image
```

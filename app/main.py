import json
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from app.models import Resource, resource_adapter

RESOURCES_FILE = Path(__file__).parent.parent / "resources" / "fhir-resources.txt"


def load_resources(path: Path) -> dict[str, dict[str, Resource]]:
    """Parse an NDJSON file into {resourceType: {id: resource}}."""
    store: dict[str, dict[str, Resource]] = defaultdict(dict)
    for line in path.read_text().splitlines():
        if line.strip():
            r = resource_adapter.validate_python(json.loads(line))
            store[r.resourceType][r.id] = r
    return store


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ponytail: whole dataset in process memory, not shared across workers; move to a DB when it outgrows that
    app.state.resources = load_resources(RESOURCES_FILE)
    yield


app = FastAPI(title="fhir-api", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# exclude_unset: omit fields the stored resource never had, instead of emitting nulls/empty lists.
@app.get(
    "/{resource_type}/{resource_id}",
    response_model=Resource,
    response_model_exclude_unset=True,
)
def read_resource(resource_type: str, resource_id: str, request: Request) -> Resource:
    resource = request.app.state.resources.get(resource_type, {}).get(resource_id)
    if resource is None:
        raise HTTPException(404, f"{resource_type}/{resource_id} not found")
    return resource

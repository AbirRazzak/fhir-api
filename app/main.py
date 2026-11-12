import json
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from app.models import AnyResource, Condition, resource_adapter
from app.responses import PatientAndConditionPair, PatientsLookupForConditionResponse

RESOURCES_FILE = Path(__file__).parent.parent / "resources" / "fhir-resources.txt"


def load_resources(path: Path) -> dict[str, dict[str, AnyResource]]:
    """Parse an NDJSON file into {resourceType: {id: resource}}."""
    store: dict[str, dict[str, AnyResource]] = defaultdict(dict)
    for line in path.read_text().splitlines():
        if line.strip():
            r = resource_adapter.validate_python(json.loads(line))
            store[r.resourceType][r.id] = r
    return store


def map_conditions_to_codes(
    resources: dict[str, dict[str, AnyResource]],
) -> dict[str, list[Condition]]:
    all_conditions: dict[str, Condition] = resources.get("Condition", {})

    condition_code_to_conditions: dict[str, list[Condition]] = defaultdict(list)
    for condition in all_conditions.values():
        if condition.code and condition.code.coding:
            code = condition.code.coding[0].code
            if code:
                condition_code_to_conditions[code].append(condition)

    return condition_code_to_conditions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ponytail: whole dataset in process memory, not shared across workers; move to a DB when it outgrows that
    resources = load_resources(RESOURCES_FILE)

    app.state.resources = resources
    app.state.condition_codes_to_conditions = map_conditions_to_codes(resources)
    yield


app = FastAPI(title="fhir-api", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/condition_patients/{condition_code}",
    response_model=PatientsLookupForConditionResponse,
)
def get_patients_for_condition(
    condition_code: str,
) -> PatientsLookupForConditionResponse:
    conditions_for_code: list[Condition] = app.state.condition_codes_to_conditions.get(
        condition_code, []
    )
    matches = []

    for condition in conditions_for_code:
        matched_patient = None
        if condition.subject:
            condition_subject_reference = condition.subject.reference
            if condition_subject_reference and condition_subject_reference.startswith(
                "Patient/"
            ):
                patient_id = condition_subject_reference.removeprefix("Patient/")
                matched_patient = app.state.resources.get("Patient", {}).get(patient_id)

        matches.append(
            PatientAndConditionPair(condition=condition, patient=matched_patient)
        )

    return PatientsLookupForConditionResponse(
        condition_code=condition_code, matches=matches
    )


# exclude_unset: omit fields the stored resource never had, instead of emitting nulls/empty lists.
@app.get(
    "/{resource_type}/{resource_id}",
    response_model=AnyResource,
    # response_model_exclude_unset=True,
)
def read_resource(
    resource_type: str, resource_id: str, request: Request
) -> AnyResource:
    resource = request.app.state.resources.get(resource_type, {}).get(resource_id)
    if resource is None:
        raise HTTPException(404, f"{resource_type}/{resource_id} not found")
    return resource

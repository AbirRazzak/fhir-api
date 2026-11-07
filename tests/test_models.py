import json
from pathlib import Path

from app.models import resource_adapter

DATA = Path(__file__).parent.parent / "resources" / "fhir-resources.txt"


def test_every_sample_resource_parses_and_round_trips():
    for line in DATA.read_text().splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        resource = resource_adapter.validate_python(raw)
        assert type(resource).__name__ == raw["resourceType"]
        assert resource.model_dump(mode="json", exclude_unset=True) == raw

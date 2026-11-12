from pydantic import BaseModel

from app.models import Condition, Patient


class PatientAndConditionPair(BaseModel):
    condition: Condition
    patient: Patient | None = None


class PatientsLookupForConditionResponse(BaseModel):
    condition_code: str
    matches: list[PatientAndConditionPair] = []

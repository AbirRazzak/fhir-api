"""Pydantic models for the FHIR resource types in resources/fhir-resources.txt.

Only the fields present in that data are modeled. Unknown fields are kept
(extra="allow"), so uploads with extra fields don't lose data.
FHIR dateTime values stay as str: FHIR allows "2015", "2015-03" or a full
timestamp, and storing them as datetime would change how they serialize.
"""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


class FhirModel(BaseModel):
    model_config = ConfigDict(extra="allow")


# Shared data types


class Coding(FhirModel):
    system: str | None = None
    code: str | None = None
    display: str | None = None


class CodeableConcept(FhirModel):
    coding: list[Coding] = []
    text: str | None = None


class Reference(FhirModel):
    reference: str | None = None
    display: str | None = None


class HumanName(FhirModel):
    use: str | None = None
    family: str | None = None
    given: list[str] = []


class Quantity(FhirModel):
    value: float | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class Attachment(FhirModel):
    contentType: str | None = None
    url: str | None = None


# Resources


class Patient(FhirModel):
    resourceType: Literal["Patient"] = "Patient"
    id: str
    name: list[HumanName] = []
    gender: str | None = None
    birthDate: date | None = None
    active: bool | None = None


class Condition(FhirModel):
    resourceType: Literal["Condition"] = "Condition"
    id: str
    clinicalStatus: CodeableConcept | None = None
    verificationStatus: CodeableConcept | None = None
    code: CodeableConcept | None = None
    subject: Reference
    onsetDateTime: str | None = None
    abatementDateTime: str | None = None
    recorder: Reference | None = None


class TimingRepeat(FhirModel):
    frequency: int | None = None
    period: float | None = None
    periodUnit: str | None = None


class Timing(FhirModel):
    repeat: TimingRepeat | None = None


class Dosage(FhirModel):
    text: str | None = None
    timing: Timing | None = None


class MedicationRequest(FhirModel):
    resourceType: Literal["MedicationRequest"] = "MedicationRequest"
    id: str
    status: str
    intent: str
    medicationCodeableConcept: CodeableConcept | None = None
    subject: Reference
    authoredOn: str | None = None
    requester: Reference | None = None
    dosageInstruction: list[Dosage] = []


class ObservationComponent(FhirModel):
    code: CodeableConcept
    valueQuantity: Quantity | None = None


class Observation(FhirModel):
    resourceType: Literal["Observation"] = "Observation"
    id: str
    status: str
    code: CodeableConcept
    subject: Reference | None = None
    effectiveDateTime: str | None = None
    performer: list[Reference] = []
    valueQuantity: Quantity | None = None
    valueString: str | None = None
    component: list[ObservationComponent] = []


class ProcedurePerformer(FhirModel):
    actor: Reference


class Procedure(FhirModel):
    resourceType: Literal["Procedure"] = "Procedure"
    id: str
    status: str
    code: CodeableConcept | None = None
    subject: Reference
    performedDateTime: str | None = None
    performer: list[ProcedurePerformer] = []


class ClinicalNote(FhirModel):
    """Not a standard FHIR resource; custom to this dataset."""

    resourceType: Literal["ClinicalNote"] = "ClinicalNote"
    id: str
    status: str | None = None
    subject: Reference | None = None
    author: Reference | None = None
    date: str | None = None
    content: str | None = None


class Binary(FhirModel):
    resourceType: Literal["Binary"] = "Binary"
    id: str
    contentType: str
    data: str | None = None  # base64


class DocumentReferenceContent(FhirModel):
    attachment: Attachment


class DocumentReference(FhirModel):
    resourceType: Literal["DocumentReference"] = "DocumentReference"
    id: str
    status: str
    type: CodeableConcept | None = None
    subject: Reference | None = None
    date: str | None = None
    author: list[Reference] = []
    content: list[DocumentReferenceContent]


# Any resource, dispatched on resourceType.
Resource = Annotated[
    Patient
    | Condition
    | MedicationRequest
    | Observation
    | Procedure
    | ClinicalNote
    | Binary
    | DocumentReference,
    Field(discriminator="resourceType"),
]
resource_adapter: TypeAdapter[Resource] = TypeAdapter(Resource)

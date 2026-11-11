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


class Resource(FhirModel):
    """Base for all resources (mirrors FHIR's abstract Resource).

    Subclasses narrow resourceType to a Literal, which the discriminated
    union below dispatches on. Declaring it here also keeps it first in JSON.
    """

    resourceType: str
    id: str


class Patient(Resource):
    resourceType: Literal["Patient"] = "Patient"
    name: list[HumanName] = []
    gender: str | None = None
    birthDate: date | None = None
    active: bool | None = None


class Condition(Resource):
    resourceType: Literal["Condition"] = "Condition"
    clinicalStatus: CodeableConcept | None = None
    verificationStatus: CodeableConcept | None = None
    code: CodeableConcept | None = None
    subject: Reference | None = None
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


class MedicationRequest(Resource):
    resourceType: Literal["MedicationRequest"] = "MedicationRequest"
    status: str | None = None
    intent: str | None = None
    medicationCodeableConcept: CodeableConcept | None = None
    subject: Reference | None = None
    authoredOn: str | None = None
    requester: Reference | None = None
    dosageInstruction: list[Dosage] = []


class ObservationComponent(FhirModel):
    code: CodeableConcept | None = None
    valueQuantity: Quantity | None = None


class Observation(Resource):
    resourceType: Literal["Observation"] = "Observation"
    status: str | None = None
    code: CodeableConcept | None = None
    subject: Reference | None = None
    effectiveDateTime: str | None = None
    performer: list[Reference] = []
    valueQuantity: Quantity | None = None
    valueString: str | None = None
    component: list[ObservationComponent] = []


class ProcedurePerformer(FhirModel):
    actor: Reference | None = None


class Procedure(Resource):
    resourceType: Literal["Procedure"] = "Procedure"
    status: str | None = None
    code: CodeableConcept | None = None
    subject: Reference | None = None
    performedDateTime: str | None = None
    performer: list[ProcedurePerformer] = []


class ClinicalNote(Resource):
    """Not a standard FHIR resource; custom to this dataset."""

    resourceType: Literal["ClinicalNote"] = "ClinicalNote"
    status: str | None = None
    subject: Reference | None = None
    author: Reference | None = None
    date: str | None = None
    content: str | None = None


class Binary(Resource):
    resourceType: Literal["Binary"] = "Binary"
    contentType: str | None = None
    data: str | None = None  # base64


class DocumentReferenceContent(FhirModel):
    attachment: Attachment | None = None


class DocumentReference(Resource):
    resourceType: Literal["DocumentReference"] = "DocumentReference"
    status: str | None = None
    type: CodeableConcept | None = None
    subject: Reference | None = None
    date: str | None = None
    author: list[Reference] = []
    content: list[DocumentReferenceContent] = []


# Any concrete resource, dispatched on resourceType.
AnyResource = Annotated[
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
resource_adapter: TypeAdapter[AnyResource] = TypeAdapter(AnyResource)

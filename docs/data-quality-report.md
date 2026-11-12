# Data quality report: `resources/fhir-resources.txt`

A review of the sample FHIR data that the API loads at startup.

## Summary

The file is well-formed. All 129 lines are valid JSON, no `resourceType`/`id` pair appears twice, and every record loads into the models in `app/models.py`. The content has problems, though:

- Two records point to patients that don't exist, and one observation isn't linked to any patient.
- The file has 78 references to 8 practitioners, but no Practitioner records.
- Two pairs of observations record the same measurement at the same time with different values.
- One Condition has no diagnosis code.
- Several codes don't match the text next to them.
- Units are written two different ways.
- The ClinicalNote and the three Binary attachments contain joke text and TV quotes, one with profanity, not clinical notes.

Some record ids contain `bad` or `dup` (`cond-nw-bad-001`, `obs-kl-bad-001`, `obs-nw-dup-001`), so some of these problems may have been planted on purpose to test error handling. Nothing in the file has been changed.

## What the file contains

| Resource type | Count |
|---|---|
| Patient | 16 |
| Condition | 23 |
| MedicationRequest | 19 |
| Observation | 57 |
| Procedure | 7 |
| ClinicalNote | 1 |
| Binary | 3 |
| DocumentReference | 3 |

Each line is one resource (newline-delimited JSON). Line numbers below refer to lines in the file.

## How the review was done

- **Script checks** (`python3 scripts/check_resources.py`): parse every line, look for repeated `resourceType`/`id` pairs, follow every `reference` to see whether the target exists, compare each `subject.display` with the named patient, and list the code systems and status values used.
- **Manual review:** I read every record and compared each code's display name with its free-text label, looked for conflicting records, and decoded the Binary attachments.
- **Not checked:** I didn't look up SNOMED or LOINC codes in their official sources; I only compared them against what I know. I didn't check the RxNorm medication codes at all.

## Findings

### 1. Broken or missing references

| Line | Record | Problem |
|---|---|---|
| 41 | `med-nw-003` | `subject` is `Patient/Noah-Wyle`. The patient's id is `noah-wyle`, and ids are case-sensitive, so the link is broken. |
| 63 | `obs-nw-006` | `subject` is `Patient/nwyle`, which doesn't exist. |
| 121 | `obs-kl-bad-001` | `subject` has only `display: "Katherine LaNasa"` and no `reference`, so it isn't linked to any patient. Its `status` is also `unknown`. |
| many | `recorder`, `requester`, `performer`, `author` | 78 references to 8 practitioners (`dr-robinavitch`, `dr-collins`, `dr-al-hashimi`, `dr-mohan`, `dr-langdon`, `dr-ellis`, `dr-whitaker`, `dr-santos`), but the file has no Practitioner records. |

**Effect on the API:** asking for all of Noah Wyle's records by his patient reference would miss lines 41 and 63. Line 121 can't be found by any patient.

### 2. Duplicate and conflicting records

| Lines | Records | Problem |
|---|---|---|
| 59, 122 | `obs-nw-002`, `obs-nw-dup-001` | Both are HbA1c for Noah Wyle at `2025-01-05T08:15:00Z`, by the same performer. The values differ: 7.8 vs 7.9. |
| 68, 70 | `obs-ti-003`, `obs-ti-005` | Both are O2 saturation for Tracy Ifeachor at `2025-01-08T09:10:00Z`. The values differ: 94 vs 96. The second is marked `amended`. In FHIR an amendment updates the original record (same id), but here the original is still `final`, so both count as current. |
| 120 | `cond-nw-bad-001` | A Condition with no `code`, so it doesn't say what the diagnosis is. |

### 3. Codes that don't match their text

| Line | Record | Code says | Text says |
|---|---|---|---|
| 115 | `proc-ti-001` | Coronary artery bypass graft (SNOMED 232717009) | Cardiac Catheterization |
| 117 | `proc-kl-001` | Admission to orthopedic department (SNOMED 305411003) | Knee Replacement Consultation |
| 116 | `proc-pb-001` | Intramuscular injection (SNOMED 76601001) | Flu Vaccination |
| 29 | `cond-td-001` | Diabetes mellitus (SNOMED 73211009, the general concept) | Type 1 Diabetes |
| 30 | `cond-ib-001` | Acute myocardial infarction, clinical status `active` | History of MI |
| 127–129 | `docref-001`–`003` | Consult note (LOINC 11488-4) | Clinical Note |

Lines 115 and 117 are the most serious: the code and the text describe different events. Line 116 is a vaccination, which FHIR would normally record as an Immunization rather than a Procedure.

### 4. Inconsistencies

- **Units:** only lines 58 and 59 give the unit system and code, e.g. `"system": "http://unitsofmeasure.org", "code": "mm[Hg]"`. The other 70 measurements (73 in total, counting blood pressure components) have only a display unit such as `"unit": "beats/minute"`, which software can't reliably compare or convert.
- **Empty dosage, line 49 (`med-fd-002`):** `dosageInstruction` is `[]`, so the tiotropium prescription has no instructions.
- **Smoking status as free text, line 72 (`obs-pb-002`):** the value is `valueString: "Former smoker, quit 2019"`. The LOINC code used (72166-2, tobacco smoking status) expects a coded answer.
- **Display name style, line 107 (`obs-kv-001`):** uses the full LOINC name ("Thyrotropin [Units/volume] in Serum or Plasma"), while every other observation uses a short name ("Heart rate", "Body Weight").

### 5. Non-clinical content

- **Line 123 (`note-robby-001`, ClinicalNote):** a plausible note that ends with "Also, if you jump on my shift, that is just rude man."
- **Lines 124–126 (`binary-001`–`003`):** the attachments decode to TV quotes, not notes:
  - `binary-001`: "Besides, if you jump on my shift, that's just rude man. - Dr. Robinavitch"
  - `binary-002`: "Does anyone tell the truth anymore or are we all just bullshitting our way through life? - Dr. Robinavitch"
  - `binary-003`: "I've worked with a few Utahs. I wish you many many Utahs in your life. - Dana"

  The "Consult note" DocumentReferences on lines 127–129 point to these, so a client opening a patient's notes would see them. Before using the data in a demo, replace them or label them as placeholders.
- **ClinicalNote is not a FHIR resource type.** Standard FHIR clients and validators will reject or ignore it. The standard way to store a note is a DocumentReference pointing at a Binary, which the file already does on lines 124–129.

## Suggested fixes

If these records aren't meant as test cases:

1. Change the references on lines 41 and 63 to `Patient/noah-wyle`. Add a `reference` on line 121, or delete the record.
2. Add Practitioner records for the 8 practitioners, or accept the dangling references and say so.
3. Remove `obs-nw-dup-001` (line 122). Replace the `obs-ti-003`/`obs-ti-005` pair with one record whose status is `amended`.
4. Give `cond-nw-bad-001` (line 120) a `code`, or delete it.
5. Fix the codes on lines 115, 117, 116 and 29 so they match the text. Change line 30 to a past or resolved MI if "history of" is what's meant.
6. Add the unit system and code to every measurement.
7. Replace the joke note and quotes, and decide whether to keep ClinicalNote or switch to DocumentReference + Binary.

If they *are* planted test cases, the API should handle them on purpose: reject or flag dangling references, a missing `subject.reference`, a missing `code`, and conflicting duplicate observations, rather than loading them silently. Today `load_resources` in `app/main.py` accepts all of them.

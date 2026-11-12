"""Scripted checks behind docs/data-quality-report.md.

Usage: python3 scripts/check_resources.py [path]   (default: resources/fhir-resources.txt)

Covers the automated half of the review. Code-vs-text mismatches and
non-clinical content were found by reading the records, not by this script.
"""

import base64
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT = Path(__file__).parent.parent / "resources" / "fhir-resources.txt"


def walk_refs(obj):
    """Yield every Reference.reference string anywhere in obj."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "reference" and isinstance(v, str):
                yield v
            else:
                yield from walk_refs(v)
    elif isinstance(obj, list):
        for x in obj:
            yield from walk_refs(x)


def walk_quantities(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "valueQuantity":
                yield v
            yield from walk_quantities(v)
    elif isinstance(obj, list):
        for x in obj:
            yield from walk_quantities(x)


def main(path: Path) -> None:
    records = []  # (line, resource)
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            print(f"line {n}: blank line")
            continue
        try:
            records.append((n, json.loads(line)))
        except json.JSONDecodeError as e:
            print(f"line {n}: invalid JSON: {e}")

    print("== Counts by resourceType")
    for t, c in Counter(r["resourceType"] for _, r in records).items():
        print(f"  {t}: {c}")

    keys = Counter((r["resourceType"], r.get("id")) for _, r in records)
    print("\n== Duplicate resourceType/id pairs")
    for k, c in keys.items():
        if c > 1:
            print(f"  {k[0]}/{k[1]} x{c}")

    print("\n== Dangling references (target not in file)")
    dangling = Counter()
    for _, r in records:
        for ref in walk_refs(r):
            t, _, i = ref.partition("/")
            if (t, i) not in keys:
                dangling[ref] += 1
    for ref, c in dangling.most_common():
        print(f"  {ref} x{c}")
    pract = sum(c for ref, c in dangling.items() if ref.startswith("Practitioner/"))
    print(f"  ({pract} Practitioner references in total)")

    print("\n== Subjects without a reference / display name mismatches")
    patients = {r["id"]: r for _, r in records if r["resourceType"] == "Patient"}
    for n, r in records:
        s = r.get("subject")
        if s is None:
            continue
        if "reference" not in s:
            print(f"  line {n} {r['id']}: subject has no reference: {s}")
            continue
        pid = s["reference"].partition("/")[2]
        if s.get("display") and pid in patients:
            name = patients[pid]["name"][0]
            full = " ".join(name.get("given", []) + [name.get("family", "")])
            if full != s["display"]:
                print(f"  line {n} {r['id']}: display {s['display']!r} != {full!r}")

    print("\n== Conflicting observations (same subject + code + time)")
    groups = defaultdict(list)
    for n, r in records:
        if r["resourceType"] == "Observation":
            code = (r.get("code", {}).get("coding") or [{}])[0].get("code")
            subj = r.get("subject", {}).get("reference")
            groups[(subj, code, r.get("effectiveDateTime"))].append((n, r))
    for (subj, code, when), rs in groups.items():
        if len(rs) > 1:
            desc = ", ".join(
                f"line {n} {r['id']} ({r.get('status')}, {r.get('valueQuantity', {}).get('value')})"
                for n, r in rs
            )
            print(f"  {subj} {code} @ {when}: {desc}")

    print("\n== Conditions without a code")
    for n, r in records:
        if r["resourceType"] == "Condition" and "code" not in r:
            print(f"  line {n} {r['id']}")

    print("\n== Empty dosageInstruction")
    for n, r in records:
        if r.get("dosageInstruction") == []:
            print(f"  line {n} {r['id']}")

    print("\n== Status values")
    for (t, s), c in Counter(
        (r["resourceType"], r.get("status")) for _, r in records
    ).items():
        if s is not None:
            print(f"  {t} {s}: {c}")

    quantities = [q for _, r in records for q in walk_quantities(r)]
    coded = sum("system" in q and "code" in q for q in quantities)
    print(
        f"\n== Units: {coded} of {len(quantities)} quantities have a UCUM system+code"
    )

    print("\n== Text content (ClinicalNote / decoded Binary)")
    for n, r in records:
        if r["resourceType"] == "ClinicalNote":
            print(f"  line {n} {r['id']}: {r.get('content')}")
        if r["resourceType"] == "Binary" and r.get("data"):
            print(f"  line {n} {r['id']}: {base64.b64decode(r['data']).decode()}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT)

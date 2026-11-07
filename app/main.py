from fastapi import FastAPI

app = FastAPI(title="fhir-api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

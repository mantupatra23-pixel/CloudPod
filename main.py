from fastapi import FastAPI

app = FastAPI(title="CloudPod Backend")

@app.get("/")
def health():
    return {"status": "CloudPod backend live"}

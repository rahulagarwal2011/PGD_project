from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="PQC Transaction Encryption API",
    description="Secure transactions using Post-Quantum Cryptography and traditional encryption.",
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to PQC Transaction Encryption API"}

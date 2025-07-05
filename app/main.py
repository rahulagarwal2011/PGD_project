from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routes import router
from app.database import init_db
from fastapi.encoders import jsonable_encoder
from app.exceptions import validation_exception_handler

init_db()

app = FastAPI(
    title="PQC Transaction Encryption API",
    description="Secure transactions using Post-Quantum Cryptography (Kyber512) and traditional RSA encryption.",
    version="1.0.0"
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to PQC Transaction Encryption API"}

# ✅ Add global exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)
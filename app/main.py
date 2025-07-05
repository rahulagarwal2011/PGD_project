from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from app.routes import router
from app.database import init_db
from app.exceptions import validation_exception_handler

# ✅ Initialize DB tables at app startup
init_db()

# ✅ Initialize FastAPI app
app = FastAPI(
    title="PQC Transaction Encryption API",
    description="Secure transactions using PQC and RSA",
    version="1.0.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
# ✅ Include API routes from routes.py
app.include_router(router)

# ✅ Root health check route
@app.get("/")
async def root():
    return {"message": "Welcome to PQC Transaction Encryption API"}

# ✅ Global exception handler for validation errors with precise error messages
app.add_exception_handler(RequestValidationError, validation_exception_handler)

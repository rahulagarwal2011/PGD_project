from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_utils.tasks import repeat_every
from app.metrics import rsa_benchmark, pqc_benchmark
from app.database import get_db
from app.benchmarks import record_benchmark
from app.routes import router
from app.database import init_db
from app.exceptions import validation_exception_handler

init_db()

app = FastAPI(
    title="PQC Transaction Encryption API",
    description="Secure transactions using PQC and RSA",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to PQC Transaction Encryption API"}

app.add_exception_handler(RequestValidationError, validation_exception_handler)

# ✅ Runs every 1 hour to persist global stats
@app.on_event("startup")
@repeat_every(seconds=3600)
def persist_global_benchmarks() -> None:
    print("[Periodic Task] Persisting global benchmarks to DB...")
    db = next(get_db())

    for benchmark, algo in [(rsa_benchmark, "RSA"), (pqc_benchmark, "PQC")]:
        summary = benchmark.summary()
        record_benchmark(
            db,
            type=f"persisted_{algo.lower()}",
            latency=summary["average_latency"],
            stddev=summary["stddev_latency"],
            min_latency=summary["min_latency"],
            max_latency=summary["max_latency"],
            throughput=summary["throughput"],
            error_rate=summary["error_rate"],
            encryption_time=0,
            algorithm=algo
        )
    print("[Periodic Task] Global benchmarks persisted successfully.")

# ✅ Runs every 5 seconds to log live snapshot
@app.on_event("startup")
@repeat_every(seconds=5)
def snapshot_live_benchmarks() -> None:
    db = next(get_db())
    for benchmark, algo in [(rsa_benchmark, "RSA"), (pqc_benchmark, "PQC")]:
        summary = benchmark.summary()
        record_benchmark(
            db,
            type=f"live_{algo.lower()}",
            latency=summary["average_latency"],
            stddev=summary["stddev_latency"],
            min_latency=summary["min_latency"],
            max_latency=summary["max_latency"],
            throughput=summary["throughput"],
            error_rate=summary["error_rate"],
            encryption_time=0,
            algorithm=algo
        )

# @app.on_event("startup")
# @repeat_every(seconds=3600)  
# def persist_global_benchmarks() -> None:
#     print("[Periodic Task] Persisting global benchmarks to DB...")
#     db = next(get_db())


#     rsa_summary = rsa_benchmark.summary()
#     record_benchmark(
#         db,
#         type="persisted_rsa",
#         latency=rsa_summary["average_latency"],
#         stddev=rsa_summary["stddev_latency"],
#         min_latency=rsa_summary["min_latency"],
#         max_latency=rsa_summary["max_latency"],
#         throughput=rsa_summary["throughput"],
#         error_rate=rsa_summary["error_rate"],
#         encryption_time=0, 
#         algorithm="RSA"
#     )


#     pqc_summary = pqc_benchmark.summary()
#     record_benchmark(
#         db,
#         type="persisted_pqc",
#         latency=pqc_summary["average_latency"],
#         stddev=pqc_summary["stddev_latency"],
#         min_latency=pqc_summary["min_latency"],
#         max_latency=pqc_summary["max_latency"],
#         throughput=pqc_summary["throughput"],
#         error_rate=pqc_summary["error_rate"],
#         encryption_time=0,
#         algorithm="PQC"
#     )

#     print("[Periodic Task] Global benchmarks persisted successfully.")
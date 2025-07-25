from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Body
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from app.models import Transaction, UserLogin, UserRegister
from app.crypto import pqc_kem_encrypt, generate_rsa_keys, rsa_hybrid_encrypt , encrypt_record
from app.database import get_db
from app.benchmarks import record_benchmark
from app.utils import hash_password, verify_password
from app.metrics import Benchmark, rsa_benchmark, pqc_benchmark
import json, sqlite3, time, math, io, logging, pandas as pd, statistics
from concurrent.futures import ProcessPoolExecutor
import asyncio


executor = ProcessPoolExecutor()
router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("bulk_encrypt.log"),
        logging.StreamHandler()
    ]
)
# def encrypt_record(record):
#     import json, time
#     from app.crypto import pqc_kem_encrypt, generate_rsa_keys, rsa_hybrid_encrypt
#     from app.models import Transaction

#     result = {
#         "success": False,
#         "data": None,
#         "rsa_time": 0,
#         "pqc_time": 0,
#         "error": False
#     }

#     try:
#         record_clean = {k: record[k] for k in Transaction.__annotations__.keys() if k in record}
#         data = json.dumps(record_clean).encode()

#         rsa_private_key, rsa_public_key = generate_rsa_keys()
#         start_rsa = time.time()
#         rsa_encrypted_key, rsa_ciphertext = rsa_hybrid_encrypt(data, rsa_public_key)
#         rsa_time = (time.time() - start_rsa) * 1000

#         start_pqc = time.time()
#         pqc_public_key, oqs_ciphertext, aes_ciphertext = pqc_kem_encrypt(data)
#         pqc_time = (time.time() - start_pqc) * 1000

#         result["success"] = True
#         result["rsa_time"] = rsa_time
#         result["pqc_time"] = pqc_time
#         result["data"] = (
#             json.dumps(record_clean),
#             rsa_encrypted_key.hex(),
#             rsa_ciphertext.hex(),
#             pqc_public_key.hex(),
#             oqs_ciphertext.hex(),
#             aes_ciphertext.hex()
#         )
#     except Exception:
#         result["error"] = True

#     return result


@router.post("/register")
async def register(user: UserRegister, db: sqlite3.Connection = Depends(get_db)):
    if not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, hash_password(user.password))
        )
        db.commit()
        return {"status": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
async def login(request: Request, db: sqlite3.Connection = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if not username or not password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Username and password required"})

    cursor = db.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()

    if not result or not verify_password(password, result[0]):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

    response = RedirectResponse(url="/main", status_code=303)
    response.set_cookie("user", username)
    return response

@router.get("/main")
async def main_page(request: Request):
    user = request.cookies.get("user")
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("main.html", {"request": request, "user": user})

@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login")
    response.delete_cookie("user")
    return response


@router.get("/secure-script")
async def secure_script(request: Request):
    user = request.cookies.get("user")
    if not user:
        return {"error": "Unauthorized"}
    return FileResponse("app/secure_js/scripts.obfuscated.js", media_type="application/javascript")


@router.post("/encrypt-transaction/")
async def encrypt_transaction(transaction: Transaction, db: sqlite3.Connection = Depends(get_db)):
    session_bm_rsa = Benchmark()
    session_bm_pqc = Benchmark()
    data = transaction.json().encode()

    rsa_time = None
    pqc_time = None


    rsa_private_key, rsa_public_key = generate_rsa_keys()
    start_rsa = time.time()
    try:
        rsa_encrypted_key, rsa_ciphertext = rsa_hybrid_encrypt(data, rsa_public_key)
        rsa_time = (time.time() - start_rsa) * 1000
        rsa_benchmark.record_latency(rsa_time)
        session_bm_rsa.record_latency(rsa_time)
    except Exception as e:
        logger.error(f"RSA encryption failed: {e}")
        rsa_benchmark.record_error()
        session_bm_rsa.record_error()


    start_pqc = time.time()
    try:
        pqc_public_key, oqs_ciphertext, aes_ciphertext = pqc_kem_encrypt(data)
        pqc_time = (time.time() - start_pqc) * 1000
        pqc_benchmark.record_latency(pqc_time)
        session_bm_pqc.record_latency(pqc_time)
    except Exception as e:
        logger.error(f"PQC encryption failed: {e}")
        pqc_benchmark.record_error()
        session_bm_pqc.record_error()


    if rsa_time is not None and pqc_time is not None:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO secure_transactions 
            (transaction_json, rsa_encrypted_key, rsa_ciphertext, pqc_public_key, oqs_ciphertext, aes_ciphertext)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.decode(),
            rsa_encrypted_key.hex(),
            rsa_ciphertext.hex(),
            pqc_public_key.hex(),
            oqs_ciphertext.hex(),
            aes_ciphertext.hex()
        ))
        db.commit()


    for bm, algo, time_taken in [(session_bm_rsa, "RSA", rsa_time), (session_bm_pqc, "PQC", pqc_time)]:
        summary = bm.summary()
        record_benchmark(
            db,
            type=f"session_{algo.lower()}",
            latency=summary["average_latency"],
            stddev=summary["stddev_latency"],
            min_latency=summary["min_latency"],
            max_latency=summary["max_latency"],
            throughput=summary["throughput"],
            error_rate=summary["error_rate"],
            encryption_time=time_taken if time_taken else 0,
            algorithm=algo
        )

    return {"status": "Transaction processed. Session benchmarks recorded."}

@router.post("/pushBulk")
async def push_bulk(
    db: sqlite3.Connection = Depends(get_db),
    file: UploadFile = File(None),
    json_batch: list = Body(None)
):
    import math, io, time, json
    import pandas as pd
    from concurrent.futures import ProcessPoolExecutor
    from app.crypto import encrypt_record
    from app.models import Transaction
    from app.metrics import Benchmark, rsa_benchmark, pqc_benchmark
    from app.benchmarks import record_benchmark
    from app.database import get_db

    BATCH_SIZE = 50000
    MAX_WORKERS = 4

    session_bm_rsa = Benchmark()
    session_bm_pqc = Benchmark()

    # Load records from CSV or JSON
    if file:
        content = await file.read()
        filename = file.filename.lower()

        if filename.endswith(".json"):
            records = json.loads(content)
        elif filename.endswith(".csv"):
            sample = content.decode(errors='ignore')[:1024]
            delimiter = ',' if sample.count(',') > sample.count(';') else ';'
            df = pd.read_csv(io.StringIO(content.decode()), delimiter=delimiter)

            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
            expected_fields = set(Transaction.__annotations__.keys())
            csv_fields = set(df.columns)

            if expected_fields != csv_fields:
                return {
                    "error": "CSV headers do not match Transaction schema",
                    "expected": sorted(expected_fields),
                    "received": sorted(csv_fields)
                }

            records = df.to_dict(orient="records")
        else:
            return {"error": "Unsupported file format."}
    elif json_batch:
        records = json_batch
    else:
        return {"error": "No data provided."}

    total_rows = len(records)
    num_batches = math.ceil(total_rows / BATCH_SIZE)
    total_success, total_fail = 0, 0

    # Function to run encryption concurrently
    async def process_batch_concurrent(batch):
        insert_data = []
        loop = asyncio.get_event_loop()
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [loop.run_in_executor(executor, encrypt_record, record) for record in batch]
            results = await asyncio.gather(*futures)

        nonlocal total_success, total_fail
        for result in results:
            if result["success"]:
                insert_data.append(result["data"])
                rsa_benchmark.record_latency(result["rsa_time"])
                pqc_benchmark.record_latency(result["pqc_time"])
                session_bm_rsa.record_latency(result["rsa_time"])
                session_bm_pqc.record_latency(result["pqc_time"])
                total_success += 1
            else:
                total_fail += 1

        return insert_data

    # Prepare database
    cursor = db.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")

    # Process all batches
    for b in range(num_batches):
        batch_records = records[b * BATCH_SIZE: (b + 1) * BATCH_SIZE]
        logger.info(f"Processing batch {b + 1}/{num_batches} with {len(batch_records)} records...")

        start_time = time.perf_counter()
        insert_data = await process_batch_concurrent(batch_records)
        duration = time.perf_counter() - start_time

        if insert_data:
            await asyncio.to_thread(cursor.executemany, """
                INSERT INTO secure_transactions 
                (transaction_json, rsa_encrypted_key, rsa_ciphertext, pqc_public_key, oqs_ciphertext, aes_ciphertext)
                VALUES (?, ?, ?, ?, ?, ?)
            """, insert_data)
            db.commit()
            logger.info(f"Batch {b + 1} inserted {len(insert_data)} records in {duration:.2f}s.")

        # # Save session metrics after each batch
        # session_bm_rsa.save()
        # session_bm_pqc.save()

    # Final session snapshot
    for bm, algo in [(session_bm_rsa, "RSA"), (session_bm_pqc, "PQC")]:
        summary = bm.summary()
        record_benchmark(
            db,
            type=f"bulk_session_{algo.lower()}",
            latency=summary["average_latency"],
            stddev=summary["stddev_latency"],
            min_latency=summary["min_latency"],
            max_latency=summary["max_latency"],
            throughput=summary["throughput"],
            error_rate=summary["error_rate"],
            encryption_time=summary["average_latency"],
            algorithm=algo
        )

    logger.info(f"Bulk processing complete. Success: {total_success}, Fail: {total_fail}")

    return {
        "status": f"Bulk load completed. {total_success} records pushed. {total_fail} records failed.",
        "total_rows": total_rows,
        "success": total_success,
        "fail": total_fail
    }



@router.get("/benchmarks/live")
async def get_live_benchmarks():
    return {
        "RSA": rsa_benchmark.summary(),
        "PQC": pqc_benchmark.summary()
    }

@router.get("/benchmarks/sessions")
async def session_benchmarks(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, algorithm, latency, stddev, min_latency, max_latency, throughput, error_rate, encryption_time, timestamp 
        FROM benchmarks
    """)
    rows = cursor.fetchall()
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "algorithm": row[1],
            "latency": row[2],
            "stddev": row[3],
            "min_latency": row[4],
            "max_latency": row[5],
            "throughput": row[6],
            "error_rate": row[7],
            "encryption_time": row[8],
            "timestamp": row[9],
        })
    return results

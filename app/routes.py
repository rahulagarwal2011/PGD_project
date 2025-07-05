from fastapi import APIRouter, Depends
from app.models import Transaction , UserLogin , UserRegister
from app.crypto import pqc_kem_encrypt, generate_rsa_keys, rsa_hybrid_encrypt
from app.database import get_db
import json
import sqlite3
import time
from app.benchmarks import record_benchmark, get_all_benchmarks
from app.utils import hash_password, verify_password

router = APIRouter()

@router.post("/encrypt-transaction/")
async def encrypt_transaction(transaction: Transaction, db: sqlite3.Connection = Depends(get_db)):
    data = json.dumps(transaction.dict()).encode()

    # PQC + AES encryption benchmark
    start_pqc = time.time()
    pqc_public_key, oqs_ciphertext, aes_ciphertext = pqc_kem_encrypt(data)
    pqc_latency = (time.time() - start_pqc) * 1000
    record_benchmark(db, "PQC+Kyber", pqc_latency)

    # RSA hybrid encryption benchmark
    start_rsa = time.time()
    rsa_private_key, rsa_public_key = generate_rsa_keys()
    rsa_encrypted_key, rsa_ciphertext = rsa_hybrid_encrypt(data, rsa_public_key)
    rsa_latency = (time.time() - start_rsa) * 1000
    record_benchmark(db, "RSA+AES Hybrid", rsa_latency)

    # Store both encryptions in database
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

    return {
        "status": "Transaction encrypted with RSA+AES hybrid and PQC, stored securely",
        "benchmarks": {
            "RSA+AES Hybrid (ms)": rsa_latency,
            "PQC+Kyber (ms)": pqc_latency
        }
    }

@router.get("/benchmarks")
async def get_benchmarks(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, type, latency FROM benchmarks")
    rows = cursor.fetchall()
    return [{"id": r[0], "type": r[1], "latency": r[2]} for r in rows]

@router.post("/register")
async def register(user: UserRegister, db: sqlite3.Connection = Depends(get_db)):
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

@router.post("/login")
async def login(user: UserLogin, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (user.username,))
    result = cursor.fetchone()

    if not result or not verify_password(user.password, result[0]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"status": "Login successful"}
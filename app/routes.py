from fastapi import APIRouter, Depends
from app.models import Transaction
from app.crypto import pqc_kem_encrypt, generate_rsa_keys, rsa_hybrid_encrypt
from app.database import get_db
import json
import sqlite3

router = APIRouter()

@router.post("/encrypt-transaction/")
async def encrypt_transaction(transaction: Transaction, db: sqlite3.Connection = Depends(get_db)):
    data = json.dumps(transaction.dict()).encode()

    # ✅ PQC + AES encryption
    pqc_public_key, oqs_ciphertext, aes_ciphertext = pqc_kem_encrypt(data)

    # ✅ RSA hybrid encryption (AES key + ciphertext)
    rsa_private_key, rsa_public_key = generate_rsa_keys()
    rsa_encrypted_key, rsa_ciphertext = rsa_hybrid_encrypt(data, rsa_public_key)

    # ✅ Store both in database
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
        "status": "Transaction encrypted with RSA+AES hybrid and PQC, stored securely"
    }

from fastapi import APIRouter
from app.models import Transaction
from app.crypto import pqc_kem_encrypt
import json

router = APIRouter()

@router.post("/encrypt-transaction/")
async def encrypt_transaction(transaction: Transaction):
    data = json.dumps(transaction.dict()).encode()
    public_key, oqs_ciphertext, aes_ciphertext = pqc_kem_encrypt(data)
    return {
        "public_key": public_key.hex(),
        "oqs_ciphertext": oqs_ciphertext.hex(),
        "aes_ciphertext": aes_ciphertext.hex()
    }

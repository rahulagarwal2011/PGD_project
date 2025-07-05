import os
import oqs
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def derive_aes_key(shared_secret):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(shared_secret)
    return digest.finalize()

def aes_encrypt(key, plaintext):
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return iv + encryptor.tag + ciphertext

def pqc_kem_encrypt(plaintext):
    with oqs.KeyEncapsulation("Kyber512") as kem:
        public_key = kem.generate_keypair()
        oqs_ciphertext, shared_secret = kem.encap_secret(public_key)
    aes_key = derive_aes_key(shared_secret)
    aes_ciphertext = aes_encrypt(aes_key, plaintext)
    return public_key, oqs_ciphertext, aes_ciphertext

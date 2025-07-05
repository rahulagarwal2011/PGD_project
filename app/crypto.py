import os
import oqs
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# ✅ Derive 256-bit AES key from shared secret using SHA256
def derive_aes_key(shared_secret):
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(shared_secret)
    return digest.finalize()
def rsa_hybrid_encrypt(plaintext, public_key):
    # Generate random AES key
    aes_key = os.urandom(32)  # 256-bit AES key

    # Encrypt AES key with RSA public key
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Encrypt plaintext with AES key
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(aes_key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    # Return RSA-encrypted AES key + AES ciphertext
    return encrypted_aes_key, iv + encryptor.tag + ciphertext
# ✅ AES-GCM encryption with random 12-byte IV
def aes_encrypt(key, plaintext):
    iv = os.urandom(12)
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend()
    ).encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return iv + encryptor.tag + ciphertext

# ✅ PQC KEM Encryption using Kyber512
def pqc_kem_encrypt(plaintext):
    with oqs.KeyEncapsulation("Kyber512") as kem:
        public_key = kem.generate_keypair()
        oqs_ciphertext, shared_secret = kem.encap_secret(public_key)
    aes_key = derive_aes_key(shared_secret)
    aes_ciphertext = aes_encrypt(aes_key, plaintext)
    return public_key, oqs_ciphertext, aes_ciphertext

# ✅ RSA 2048-bit key generation
def generate_rsa_keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key

# ✅ RSA Encryption using OAEP padding
def rsa_encrypt(data: bytes, public_key):
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def rsa_decrypt(ciphertext: bytes, private_key):
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
def pqc_kem_decrypt(oqs_ciphertext, secret_key, aes_ciphertext):
    # Load Kyber512 KEM
    with oqs.KeyEncapsulation("Kyber512") as kem:
        kem.secret_key = secret_key  # Set the secret key

        # Decapsulate to get the shared secret
        shared_secret = kem.decap_secret(oqs_ciphertext)

    # Derive AES key from shared secret
    aes_key = derive_aes_key(shared_secret)

    # Decrypt AES-GCM ciphertext
    iv = aes_ciphertext[:12]
    tag = aes_ciphertext[12:28]
    ciphertext = aes_ciphertext[28:]

    decryptor = Cipher(
        algorithms.AES(aes_key),
        modes.GCM(iv, tag),
        backend=default_backend()
    ).decryptor()

    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext    
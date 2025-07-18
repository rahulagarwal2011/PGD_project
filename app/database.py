import sqlite3

# Database connection dependency
def get_db():
    conn = sqlite3.connect("creditcard.db", check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

# Initialize DB schema (run once)
def init_db():
    conn = sqlite3.connect("creditcard.db")
    cursor = conn.cursor()

    # Create secure_transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS secure_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_json TEXT,
        rsa_encrypted_key TEXT,
        rsa_ciphertext TEXT,
        pqc_public_key TEXT,
        oqs_ciphertext TEXT,
        aes_ciphertext TEXT
    )
    """)

    # Create benchmarks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS benchmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        latency REAL,
        stddev REAL,
        min_latency REAL,
        max_latency REAL,
        throughput REAL,
        error_rate REAL,
        encryption_time REAL,
        algorithm TEXT, -- 'RSA' or 'PQC'
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

import time
import sqlite3

def record_benchmark(db, type, latency):
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO benchmarks (type, latency) VALUES (?, ?)",
        (type, latency)
    )
    db.commit()

def get_all_benchmarks(db):
    cursor = db.cursor()
    cursor.execute("SELECT type, latency FROM benchmarks")
    return cursor.fetchall()

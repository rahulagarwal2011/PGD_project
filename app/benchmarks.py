from fastapi import APIRouter, Depends
import sqlite3
import statistics
from app.database import get_db
from app.metrics import rsa_benchmark, pqc_benchmark , Benchmark

router = APIRouter()
rsa_session_benchmark = Benchmark()
pqc_session_benchmark = Benchmark()

def record_benchmark(db, type, latency, stddev, min_latency, max_latency, throughput, error_rate, encryption_time, algorithm):
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO benchmarks 
        (type, latency, stddev, min_latency, max_latency, throughput, error_rate, encryption_time, algorithm)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (type, latency, stddev, min_latency, max_latency, throughput, error_rate, encryption_time, algorithm))
    db.commit()

@router.get("/benchmarks/live")
async def get_live_benchmarks():
    rsa_summary = rsa_benchmark.summary()
    pqc_summary = pqc_benchmark.summary()

    return {
        "RSA": rsa_summary,
        "PQC": pqc_summary
    }
    
@router.get("/benchmarks/history")
async def get_historical_benchmarks(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    results = []

    for algo in ["RSA", "PQC"]:
        cursor.execute("SELECT latency, stddev, min_latency, max_latency, throughput, error_rate, encryption_time FROM benchmarks WHERE algorithm = ?", (algo,))
        rows = cursor.fetchall()
        if not rows:
            continue

        latencies = [row[0] for row in rows]
        stddevs = [row[1] for row in rows]
        min_latencies = [row[2] for row in rows]
        max_latencies = [row[3] for row in rows]
        throughputs = [row[4] for row in rows]
        error_rates = [row[5] for row in rows]
        encryption_times = [row[6] for row in rows]

        results.append({
            "algorithm": algo,
            "avg_latency": sum(latencies) / len(latencies),
            "avg_stddev": sum(stddevs) / len(stddevs),
            "avg_min_latency": sum(min_latencies) / len(min_latencies),
            "avg_max_latency": sum(max_latencies) / len(max_latencies),
            "avg_throughput": sum(throughputs) / len(throughputs),
            "avg_error_rate": sum(error_rates) / len(error_rates),
            "avg_encryption_time": sum(encryption_times) / len(encryption_times)
        })
    
    return results    
@router.get("/benchmarks/live")
async def get_live_benchmarks():
    return {
        "RSA": rsa_benchmark.summary(),
        "PQC": pqc_benchmark.summary()
    }
    
@router.get("/benchmarks/sessions")
async def get_session_benchmarks(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, type, latency, stddev, min_latency, max_latency, throughput, error_rate, encryption_time, algorithm, timestamp 
        FROM benchmarks
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]
    
        
def get_all_benchmarks(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM benchmarks")
    return cursor.fetchall()
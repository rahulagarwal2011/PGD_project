# Quantum Encryption Dashboard

This project is a sleek, containerized web portal for securely uploading, encrypting, and benchmarking transactions using both RSA and Post-Quantum Cryptography (PQC).

## Key Highlights

- **Single transaction** and **bulk upload** modes (JSON/CSV)
- Encryption via **RSA + PQC**
- **Real-time and session-level benchmarking**
- **SQLite** persistent storage
- **Dockerized deployment** for portability and isolation
- **Modern, animated cyberpunk UI** with fade feedback

---

## Why Docker?

- **Consistency** across development, testing, and production environments
- **Isolation** from host system dependencies
- **Portability**: single container works anywhere Docker runs
- **Scalability**: easily orchestrate multiple micro-services
- Simplified installation—just `docker build` and `docker run`

---

## Feature-by-Feature Advantages

### Encryption (RSA + PQC)
- Dual encryption algorithms ensure compatibility (classical RSA) and future-readiness (PQC).
- Each transaction stores both ciphertexts with separate benchmarking.
- Highly secure: PQC prevents vulnerabilities against quantum-enabled attackers.

### Benchmarking
- **Live metrics**: updated every 5 seconds; view average latency, throughput, error rate.
- **Session benchmarks**: summary persisted after each upload session.
- Insights into performance variability, error rate, min/max latency.

### Bulk Processing & Concurrency
- `/pushBulk` reads full CSV or JSON in batches.
- Utilizes **async I/O + ProcessPoolExecutor** for parallel encryption.
- Efficient even with large files; errors logged per row.

### SQLite Backend
- Lightweight and zero-configuration database.
- Stores encrypted transactions and benchmark history.
- Fast inserts and straightforward schema.

### Frontend UX
- Tabbed interface to switch between load, session, and live views.
- Fade-in/out `status` messages for push success or failure.
- Responsive dark theme with cyberpunk neon aesthetic.

---

## How Each Route Works

### POST /encrypt-transaction/
- Input: JSON mapped to Pydantic `Transaction` model.
- Encrypts sequentially: RSA then PQC.
- Measures latency and updates in-memory and session benchmarks.
- Persists encrypted record and writes session benchmark to DB.

### POST /pushBulk
- Accepts file upload (.csv or .json).
- Parses records, strips unwanted columns, ensures schema match.
- Processes records concurrently via `encrypt_record` invoked in worker pool.
- Tracks per-session totals (success/failure).
- Persists encrypted batch and writes session summary to DB.
- Returns JSON with `success` and `fail` counts.

### GET /benchmarks/live
- Returns current `rsa_benchmark` and `pqc_benchmark` summaries from memory.
- Includes average latency, stddev, throughput, error rate.
- Auto-snapshot every 5 seconds to DB with Docker event scheduler.

### GET /benchmarks/sessions
- Queries stored benchmarks table in SQLite.
- Returns list of past sessions including persisted live snapshots.

---

## Encryption & Benchmarking Flow

1. **Encryption step**: generate key, encrypt data, measure start/stop times.
2. **Error handling**: exceptions logged per algorithm (RSA or PQC).
3. **Benchmark update**: both in-memory (`rsa_benchmark`) and session-level.
4. **Database persists**: transaction + summary, either per record or at the end of bulk.
5. **Periodic snapshot**: scheduler captures live metrics every N seconds to DB.

---

## Concurrency & Batch Management

- **Batch size** defined, default 50k. Processed in chunks.
- Uses FastAPI's async handler + background worker processes.
- Each record encrypted independently; failures do not block others.
- Worker functions must be top-level to ensure picklability.
- Commit after each batch to persist partial progress and reduce rollback risk.

---

## Docker Workflow

### Dockerfile (example)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn cryptography pandas
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Usage:
```bash
docker build -t quantum-dashboard .
docker run -d -p 8000:8000 quantum-dashboard
```

**Advantages**:
- Encapsulates dependencies
- Clean environment per deployment
- Reduces "works on my machine" issues

---

## Project Structure

```
.
├── Dockerfile
├── main.py
├── routes.py
├── crypto.py
├── metrics.py
├── benchmarks.py
├── database.py
├── templates/
│   ├── login.html
│   └── main.html
├── static/
│   └── styles.css
└── README.md
```

---

## Putting It All Together

- Users log in, upload single or bulk transactions via the dashboard.
- Each transaction is encrypted with both schemes, performance measured.
- Frontend displays live stats and historical session metrics.
- Docker ensures portability, isolation, and ease of deployment.
- SQLite stores data and periodic snapshot records.
- Encryption logic and UI design are harmonized for both usability and security.

# Stage 1: Build liboqs and liboqs-python
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y git build-essential cmake libssl-dev swig

# Uninstall any pre-installed oqs
RUN pip uninstall -y oqs || true

# Clone and build liboqs
RUN git clone --branch main https://github.com/open-quantum-safe/liboqs.git /liboqs && \
    cd /liboqs && mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local -DBUILD_SHARED_LIBS=ON .. && \
    make -j$(nproc) && make install

# Stage 2: Final runtime image
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y libssl-dev git build-essential cmake swig

# Copy built liboqs from builder
COPY --from=builder /usr/local /usr/local

# Set LD_LIBRARY_PATH for liboqs runtime linking
ENV LD_LIBRARY_PATH=/usr/local/lib

# Clone and build liboqs-python in runtime environment for correct linking
RUN git clone --branch main https://github.com/open-quantum-safe/liboqs-python.git /liboqs-python && \
    cd /liboqs-python && \
    pip install .

# Verify installation
RUN python -c "import oqs; print(dir(oqs))"

# Set workdir
WORKDIR /app

# Copy requirements first for cache optimization
COPY requirements.txt .

# Install Python dependencies (no oqs here)
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY . .

COPY static ./static

# Expose port
EXPOSE 8000

# Command to run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

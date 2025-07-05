# Stage 1: Build liboqs from source (if prebuilt not available)
FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y git build-essential cmake libssl-dev

# Clone and build liboqs
RUN git clone --branch main https://github.com/open-quantum-safe/liboqs.git /liboqs && \
    cd /liboqs && mkdir build && cd build && \
    cmake -DCMAKE_INSTALL_PREFIX=/usr/local .. && \
    make && make install

# Install liboqs-python in builder
RUN pip install --upgrade pip setuptools wheel && \
    pip install oqs

# Stage 2: Final minimal image
FROM python:3.10-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y libssl-dev

# Copy liboqs built in builder
COPY --from=builder /usr/local /usr/local

# Set workdir
WORKDIR /app

# Copy requirements first for cache optimization
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command to run app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

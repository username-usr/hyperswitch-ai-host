# ==========================================
# STAGE 1: The Builder Environment
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system compilation assets required for heavy C++ wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compile and isolate packages into the user local directory space
RUN pip install --no-cache-dir --user -r requirements.txt


# ==========================================
# STAGE 2: The Minimalist Runtime Space
# ==========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Pull only the compiled libraries from the builder stage
COPY --from=builder /root/.local /root/.local

# Ensure the system binary path points to the newly imported packages
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Copy the microservice source modules
COPY config/ ./config/
COPY app/ ./app/

# Copy your hardware-optimized 2.2GB local SLM layer
COPY models/ ./models/

# Open the communication gate for port 8000
EXPOSE 8000

# Execute the non-blocking production server gateway loop
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
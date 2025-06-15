FROM python:3.11-slim

# Install system dependencies for HFT performance
RUN apt-get update && apt-get install -y \
    gcc g++ \
    libnuma-dev \
    libpcap-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build C extensions for maximum performance
RUN python setup.py build_ext --inplace

# Create non-root user for security
RUN useradd -m -u 1000 hftuser && chown -R hftuser:hftuser /app
USER hftuser

# Expose monitoring ports
EXPOSE 8080 9090

# Set environment variables for production
ENV PYTHONPATH=/app
ENV HFT_MODE=production
ENV OMP_NUM_THREADS=1

# Run the application
CMD ["python", "market_data_simulator.py"]
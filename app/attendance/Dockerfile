FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libboost-python-dev \
    libopenblas-dev \
    liblapack-dev \
    libjpeg-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install opencv-python-headless

# Copy the service code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
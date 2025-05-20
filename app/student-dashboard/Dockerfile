FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy the current directory contents to /app
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
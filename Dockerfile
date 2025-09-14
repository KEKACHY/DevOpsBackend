# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies required for psycopg2 and other packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy the requirements file first to leverage Docker cache
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Alternative if you want to use psycopg2-binary instead (no system dependencies needed):
# RUN pip install --no-cache-dir psycopg2-binary==2.9.6

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port the app runs on
EXPOSE 8003

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

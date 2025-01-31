FROM python:3.10-slim

RUN apt-get update && apt-get install -y git wget && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./rag_service
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
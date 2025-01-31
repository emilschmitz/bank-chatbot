#!/bin/bash
echo "Starting data ingestion..."
python rag_service/ingest.py
echo "Starting RAG CLI..."
python rag_service/rag_cli.py
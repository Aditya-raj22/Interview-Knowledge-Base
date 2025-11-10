#!/bin/bash
# Start the Interview KB UI server

echo "Starting Interview Knowledge Base UI..."
echo "Server will be available at: http://localhost:8000"
echo ""

cd ui
python app.py

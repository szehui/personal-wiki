#!/bin/bash
echo "🚀 Starting manual clippings ingestion..."
cd ~/wiki
python3 scripts/ingest_clippings.py
echo "✅ Ingestion complete!"

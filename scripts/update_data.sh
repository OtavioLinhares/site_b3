#!/bin/bash

# Define project directory
PROJECT_DIR="/home/otaviopereiralinhares/.gemini/antigravity/scratch/analise_acoes"
LOG_FILE="$PROJECT_DIR/update_log.txt"

# Navigate to project directory
cd "$PROJECT_DIR" || exit

# Log start time
echo "========================================" >> "$LOG_FILE"
echo "Update started at $(date)" >> "$LOG_FILE"

# 1. Run Pipeline (Fetch new data from Fundamentus/Yahoo)
echo "Running Pipeline..." >> "$LOG_FILE"
/usr/bin/python3 etl/pipeline.py >> "$LOG_FILE" 2>&1

# 2. Regenerate Rankings (Apply logic filters)
echo "Regenerating Rankings..." >> "$LOG_FILE"
/usr/bin/python3 regen_rankings.py >> "$LOG_FILE" 2>&1

# Log end time
echo "Update finished at $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

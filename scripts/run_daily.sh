#!/bin/bash

# Configuration
PROJECT_DIR="/home/otaviopereiralinhares/.gemini/antigravity/scratch/analise_acoes"
VENV_ACTIVATE="/home/otaviopereiralinhares/miniconda3/envs/venv/bin/activate"
LOG_DIR="$PROJECT_DIR/logs"

# Ensure Log Dir Exists
mkdir -p "$LOG_DIR"

# Date for Log File
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/run_daily_$TODAY.log"

echo "Starting Daily Update: $TODAY" >> "$LOG_FILE"

# Activate Virtual Environment
source "$VENV_ACTIVATE"

# Navigate to Project Dir
cd "$PROJECT_DIR" || { echo "Failed to cd to $PROJECT_DIR" >> "$LOG_FILE"; exit 1; }

# Run Pipeline
# Note: In production, remove --limit or set it high
python etl/pipeline.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Pipeline Completed Successfully." >> "$LOG_FILE"
else
    echo "Pipeline Failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "Finished at $(date)" >> "$LOG_FILE"
exit $EXIT_CODE

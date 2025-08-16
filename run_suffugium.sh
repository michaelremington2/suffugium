#!/bin/bash
# run_suffugium.sh
# A quick script to run the Suffugium model

# Exit if any command fails
set -e

# Define paths
BASE_DIR="/home/micha/Documents/suffugium"
model_DIR="$BASE_DIR/src/suffugium"
CONFIG_FILE="$BASE_DIR/config.yaml"
OUTPUT_DIR="$BASE_DIR/results"
db_path="$OUTPUT_DIR/suffugium.db"
SEED=42
sim_id=1
keep_data=5

# Activate venv if you use one
# source "$BASE_DIR/.venv/bin/activate"

python "$model_DIR/run_model.py" \
    --config "$CONFIG_FILE" \
    --output "$OUTPUT_DIR" \
    --sim_id $sim_id \
    --seed $SEED \
    --db_path "$db_path" \
    --keep_data $keep_data
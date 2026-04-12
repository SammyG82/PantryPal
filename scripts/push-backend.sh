#!/bin/bash
# Syncs backend/ to hf-space/ and pushes to HuggingFace Space

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$SCRIPT_DIR/.."
HF="$ROOT/hf-space"

echo "Syncing backend files to hf-space..."
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='model/' \
  "$ROOT/backend/" "$HF/"

echo "Pushing to HuggingFace..."
cd "$HF"
git add -A
git diff --cached --quiet && echo "No changes to push." && exit 0
git commit -m "sync backend from main repo"
git push

echo "Done."

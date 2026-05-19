#!/bin/bash
# Post-edit hook: run ruff check on edited Python files
# Exits 0 always (non-blocking) — just reports issues as feedback

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only run on Python files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# Only run if file exists (might be a new file being written)
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

cd /Users/forrest/Documents/aleq-production/stargate-lite || exit 0
source venv/bin/activate 2>/dev/null

# Run ruff check (lint only, don't auto-fix — just report)
LINT_OUTPUT=$(ruff check "$FILE_PATH" 2>&1)
if [[ $? -ne 0 ]]; then
  echo "ruff: $LINT_OUTPUT"
fi

exit 0

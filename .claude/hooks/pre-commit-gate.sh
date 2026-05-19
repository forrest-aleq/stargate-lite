#!/bin/bash
# Pre-commit hook: run tests before allowing git commit
# Exit 2 = block the tool call, exit 0 = allow it

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Only intercept git commit commands
if ! echo "$COMMAND" | grep -qE '^git commit'; then
  exit 0
fi

cd /Users/forrest/Documents/aleq-production/stargate-lite || exit 0
source venv/bin/activate 2>/dev/null

# Run quick test suite
TEST_OUTPUT=$(python -m pytest tests/ -x -q --tb=line 2>&1)
TEST_EXIT=$?

if [[ $TEST_EXIT -ne 0 ]]; then
  echo "Tests failed — fix before committing:" >&2
  echo "$TEST_OUTPUT" | tail -20 >&2
  exit 2
fi

exit 0

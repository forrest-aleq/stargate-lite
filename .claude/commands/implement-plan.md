Implement the plan specified by $ARGUMENTS. This could be a plan file path, a Linear issue reference, or an inline description.

## Before Writing Any Code

1. **Read the full plan**: If a file path is given, read it entirely. If a Linear issue, fetch it. Understand ALL items before starting.
2. **Map dependencies**: Identify the order of implementation — which files depend on which.
3. **Read existing code**: For every file you'll modify, read it first. Understand what exists.
4. **Count the items**: If the plan says "11 providers" or "8 commits" — verify you're covering ALL of them. Do not skip any.

## Implementation Rules

- Implement in dependency order (foundations first, then consumers)
- After EACH logical group of changes (e.g., one commit's worth), run:
  ```
  source venv/bin/activate && python -m pytest tests/ -x -q
  ```
  Fix any failures before moving to the next group.
- Follow existing patterns in the codebase — match the style of adjacent code
- Use errors from `app/errors.py`, logging from `app/logging_config`, structured logs with `log_event=`
- Guardian enforces 650-line file limit — split proactively if a file is approaching the limit
- Do NOT bump VERSION or update CHANGELOG.md unless the plan explicitly says to

## Verification Gates

After ALL implementation is complete:
1. Run the full test suite: `source venv/bin/activate && python -m pytest tests/ -v`
2. Run pre-commit: `source venv/bin/activate && pre-commit run --all-files`
3. Fix any failures — do NOT report done with failing checks
4. Run `git diff` and review your changes — confirm nothing was accidentally removed or broken

## Reporting

When done, provide:
- Summary of what was implemented (with file paths)
- Test results (passing count)
- Any items from the plan that were intentionally deferred (with explanation)
- Any new issues discovered during implementation

Perform a thorough, ironclad audit of $ARGUMENTS (or the current branch changes vs main if no argument given).

## Process

1. **Scope**: Identify all files to audit. If a path was given, audit that path recursively. If no argument, run `git diff main --name-only` to get changed files.

2. **Static analysis**: Run these commands and report any issues:
   ```
   source venv/bin/activate
   ruff check <target files>
   mypy --strict --ignore-missing-imports --disable-error-code=misc <target files>
   ```

3. **Code review**: For EACH file, read the full file and check:
   - Error handling uses `app/errors.py` errors (not bare exceptions)
   - Logging uses `get_logger(__name__)` with `log_event=` for structured logging
   - No credentials or secrets in error messages or logs
   - No `print()` statements (use logger)
   - Type annotations are complete (mypy --strict compatible)
   - Functions don't exceed guardian size limits

4. **Contract verification**: If the audit involves models, connectors, or registry:
   - Cross-reference every field in docs against actual code
   - Verify capability keys in registry match connector method signatures
   - Check that handler functions accept (org_id, user_id, args) properly
   - Verify OAuth flows have signed state parameters

5. **Cross-reference check**: For ANY claim in documentation:
   - Count things manually (platforms, capabilities, endpoints)
   - Don't trust comments — verify against the actual implementation
   - Flag stale counts, wrong file paths, outdated descriptions

## Output Format

Produce a structured report:

### CRITICAL (must fix before merge)
- [file:line] Description of issue

### WARNING (should fix)
- [file:line] Description of issue

### INFO (suggestions)
- [file:line] Description of suggestion

### Summary
- Files audited: N
- Issues found: N critical, N warning, N info
- Tests passing: yes/no (run `python -m pytest tests/ -x -q`)

Do NOT mark anything as "looks fine" without showing the specific code that confirms it. Zero assumptions — only verified facts.

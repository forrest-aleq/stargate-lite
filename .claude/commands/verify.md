Run a comprehensive verification checkpoint on the current state of the working tree.

## Steps

1. **Git status**: Show all staged, unstaged, and untracked changes
   ```
   git status
   git diff --stat
   ```

2. **Test suite**: Run full tests and report results
   ```
   source venv/bin/activate && python -m pytest tests/ -v --tb=short
   ```

3. **Pre-commit hooks**: Run all hooks
   ```
   source venv/bin/activate && pre-commit run --all-files
   ```

4. **Regression check**: If there are changes vs the last commit:
   ```
   git diff HEAD
   ```
   Review the diff and flag:
   - Any lines REMOVED that weren't part of the intended changes
   - Any functions or imports that disappeared
   - Any registry entries that were dropped
   - Any test files that lost test cases

5. **Guardian check**: For any modified Python files, verify:
   - File is under 650 lines (`wc -l`)
   - No function exceeds the size limit

6. **Import check**: Quick sanity check that the app loads
   ```
   source venv/bin/activate && python -c "from app.registry import CAPABILITY_REGISTRY; print(f'{len(CAPABILITY_REGISTRY)} capabilities loaded')"
   ```

## Output

Report a clear pass/fail status:
- Tests: PASS/FAIL (N passed, N failed)
- Pre-commit: PASS/FAIL
- Regressions: NONE FOUND / [list of concerns]
- Guardian: PASS/FAIL
- Import check: PASS/FAIL (N capabilities)

If anything fails, explain what failed and suggest fixes.

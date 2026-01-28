#!/usr/bin/env python3
"""Guardian: Catches real Python bugs without blocking your flow.

Configurable via guardian_config.toml.
"""

from __future__ import annotations

import ast
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_FILE = "guardian_config.toml"


@dataclass
class Config:
    """Configuration from guardian_config.toml."""

    src_root: Path = field(default_factory=lambda: Path("src"))
    exclude_dirs: tuple[str, ...] = ("tests", "scripts", "__pycache__")

    max_file_lines: int = 500
    max_function_lines: int = 50
    custom_file_limits: dict[str, int] = field(default_factory=dict)

    async_only_dirs: tuple[str, ...] = ()
    sync_allowed_modules: tuple[str, ...] = ()
    blocking_calls: frozenset[str] = frozenset(
        {
            "time.sleep",
            "subprocess.run",
            "subprocess.call",
            "subprocess.check_output",
            "os.system",
        }
    )

    blocked_network_libs: frozenset[str] = frozenset()
    network_allowed_dirs: tuple[str, ...] = ()

    ban_type_ignore: bool = True
    any_allowed_paths: tuple[str, ...] = ()

    ban_print: bool = True
    ban_bare_except: bool = True
    ban_mutable_defaults: bool = True
    ban_star_imports: bool = True
    ban_assert: bool = True  # assert is for tests, not validation
    ban_global: bool = False
    banned_markers: tuple[str, ...] = ("todo", "fixme")

    # CodeRabbit-inspired checks
    ban_naive_datetime: bool = True
    ban_unsafe_singleton: bool = True
    ban_next_without_default: bool = True
    ban_fstring_injection: bool = True

    ban_mock_data: bool = True
    mock_patterns: tuple[str, ...] = (
        "mock_",
        "_mock",
        "fake_",
        "_fake",
        "dummy_",
        "_dummy",
        "test_user",
        "test_email",
        "test_password",
        "example@",
        "@example.com",
        "@test.com",
        "placeholder",
        "sample_",
        "hardcoded",
        "changeme",
        "replace_me",
        "your_",
        "xxx",
        "lorem ipsum",
        "foo_bar",
        "asdf",
    )

    require_subprocess_check: bool = True
    ban_subprocess_shell: bool = True
    ban_eval_exec: bool = True


def load_config() -> Config:
    """Load config from TOML."""
    path = Path(CONFIG_FILE)
    if not path.exists():
        return Config()

    with open(path, "rb") as f:
        data = tomllib.load(f)

    cfg = Config()

    if p := data.get("project"):
        if v := p.get("src_root"):
            cfg.src_root = Path(v)
        if v := p.get("exclude_dirs"):
            cfg.exclude_dirs = tuple(v)

    if lim := data.get("limits"):
        cfg.max_file_lines = lim.get("max_file_lines", cfg.max_file_lines)
        cfg.max_function_lines = lim.get("max_function_lines", cfg.max_function_lines)
        if v := lim.get("custom_file_limits"):
            cfg.custom_file_limits = dict(v)

    if a := data.get("async"):
        if v := a.get("async_only_dirs"):
            cfg.async_only_dirs = tuple(v)
        if v := a.get("sync_allowed_modules"):
            cfg.sync_allowed_modules = tuple(v)
        if v := a.get("blocking_calls"):
            cfg.blocking_calls = frozenset(v)

    if imp := data.get("imports"):
        if v := imp.get("blocked_network_libs"):
            cfg.blocked_network_libs = frozenset(v)
        if v := imp.get("network_allowed_dirs"):
            cfg.network_allowed_dirs = tuple(v)

    if t := data.get("typing"):
        cfg.ban_type_ignore = t.get("ban_type_ignore", cfg.ban_type_ignore)
        if v := t.get("any_allowed_paths"):
            cfg.any_allowed_paths = tuple(v)

    if q := data.get("quality"):
        cfg.ban_print = q.get("ban_print", cfg.ban_print)
        cfg.ban_bare_except = q.get("ban_bare_except", cfg.ban_bare_except)
        cfg.ban_mutable_defaults = q.get("ban_mutable_defaults", cfg.ban_mutable_defaults)
        cfg.ban_star_imports = q.get("ban_star_imports", cfg.ban_star_imports)
        cfg.ban_assert = q.get("ban_assert", cfg.ban_assert)
        cfg.ban_global = q.get("ban_global", cfg.ban_global)
        if "banned_markers" in q:
            cfg.banned_markers = tuple(q["banned_markers"])
        cfg.ban_mock_data = q.get("ban_mock_data", cfg.ban_mock_data)
        if v := q.get("mock_patterns"):
            cfg.mock_patterns = tuple(v)
        cfg.ban_naive_datetime = q.get("ban_naive_datetime", cfg.ban_naive_datetime)
        cfg.ban_unsafe_singleton = q.get("ban_unsafe_singleton", cfg.ban_unsafe_singleton)
        cfg.ban_next_without_default = q.get(
            "ban_next_without_default", cfg.ban_next_without_default
        )
        cfg.ban_fstring_injection = q.get("ban_fstring_injection", cfg.ban_fstring_injection)

    if s := data.get("security"):
        cfg.require_subprocess_check = s.get(
            "require_subprocess_check", cfg.require_subprocess_check
        )
        cfg.ban_subprocess_shell = s.get("ban_subprocess_shell", cfg.ban_subprocess_shell)
        cfg.ban_eval_exec = s.get("ban_eval_exec", cfg.ban_eval_exec)

    return cfg


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def iter_py_files(root: Path, exclude: tuple[str, ...]) -> Iterable[Path]:
    """Iterate Python files, excluding specified dirs."""
    if not root.exists():
        return
    for p in root.rglob("*.py"):
        if p.is_file() and not any(ex in p.parts for ex in exclude):
            yield p


def path_matches(path: Path, patterns: tuple[str, ...]) -> bool:
    """Check if path matches any pattern (substring)."""
    s = str(path)
    return any(p in s for p in patterns)


def get_call_name(node: ast.Call) -> str:
    """Get full call name like 'time.sleep'."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts: list[str] = []
        current: ast.expr = node.func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def get_decorator_name(dec: ast.expr) -> str:
    """Get decorator name."""
    if isinstance(dec, ast.Name):
        return dec.id
    if isinstance(dec, ast.Attribute):
        return dec.attr
    return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_file_size(path: Path, lines: list[str], cfg: Config) -> list[str]:
    """File size check."""
    limit = cfg.max_file_lines
    for pattern, lim in cfg.custom_file_limits.items():
        if str(path).endswith(pattern):
            limit = lim
            break
    if len(lines) > limit:
        return [f"{path}: {len(lines)} lines (max {limit}). Split it up."]
    return []


def check_banned_markers(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for TODO/FIXME markers."""
    low = content.lower()
    for marker in cfg.banned_markers:
        if marker in low:
            return [f"{path}: Contains '{marker.upper()}'. Finish it before committing."]
    return []


def check_mock_data(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for mock/fake/placeholder data in production code."""
    if not cfg.ban_mock_data:
        return []
    low = content.lower()
    lines = content.splitlines()
    for pattern in cfg.mock_patterns:
        if pattern.lower() in low:
            # Find the line number
            for i, line in enumerate(lines, 1):
                if pattern.lower() in line.lower():
                    return [
                        f"{path}:{i}: Mock/fake data '{pattern}'. Replace with real implementation."
                    ]
    return []


def check_print(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for print()."""
    if cfg.ban_print and "print(" in content:
        return [f"{path}: Contains print(). Use logging."]
    return []


def check_type_ignore(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for # type: ignore."""
    if cfg.ban_type_ignore and "# type: ignore" in content:
        return [f"{path}: Contains '# type: ignore'. Fix the types."]
    return []


def check_any_import(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for typing.Any."""
    has_any = "from typing import Any" in content or "typing.Any" in content
    if has_any and not path_matches(path, cfg.any_allowed_paths):
        return [f"{path}: Uses 'Any'. Use explicit types."]
    return []


def check_naive_datetime(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for naive datetime usage (timezone-unaware)."""
    if not cfg.ban_naive_datetime:
        return []
    violations = []
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        # Skip comments
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        # Check for datetime.now() without timezone argument
        if "datetime.now()" in line:
            violations.append(
                f"{path}:{i}: datetime.now() without timezone. Use datetime.now(UTC)."
            )
        # Check for deprecated utcnow()
        if ".utcnow()" in line:
            violations.append(
                f"{path}:{i}: datetime.utcnow() is deprecated. Use datetime.now(UTC)."
            )
    return violations


def check_unsafe_singleton(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for thread-unsafe singleton pattern."""
    if not cfg.ban_unsafe_singleton:
        return []
    # Pattern: global var + if var is None: var = ... without Lock
    # Valid patterns (double-check locking):
    #   if _x is None: with lock: if _x is None: _x = ...
    #   with lock: if _x is None: _x = ...
    lines = content.splitlines()
    violations = []

    for i, line in enumerate(lines):
        # Look for "if _something is None:" pattern
        if "is None:" in line and line.lstrip().startswith("if _"):
            # Check context: 5 lines before and 5 lines after
            context_start = max(0, i - 5)
            context_end = min(len(lines), i + 6)
            context_before = "\n".join(lines[context_start:i])
            context_after = "\n".join(lines[i:context_end])

            has_global = "global _" in context_before
            # Lock can be before OR after (double-check pattern)
            has_lock_before = "with " in context_before and "lock" in context_before.lower()
            has_lock_after = "with " in context_after and "lock" in context_after.lower()
            has_lock = has_lock_before or has_lock_after

            if has_global and not has_lock:
                violations.append(
                    f"{path}:{i + 1}: Potential thread-unsafe singleton. "
                    "Use lock for thread-safe initialization."
                )
    return violations


def check_fstring_injection(path: Path, content: str, cfg: Config) -> list[str]:
    """Check for potential SQL/GraphQL injection via f-strings."""
    if not cfg.ban_fstring_injection:
        return []
    violations = []
    lines = content.splitlines()

    # SQL/GraphQL keywords that indicate a query (must appear at start-ish of query)
    query_starters = ("select ", "insert ", "update ", "delete ", "mutation ", "query {")

    # Track if we're in a multiline string that looks like a query
    in_query_string = False
    query_start_line = 0

    for i, line in enumerate(lines, 1):
        lower = line.lower()
        stripped_lower = lower.lstrip()

        # Detect query string starts (multiline)
        if '"""' in lower or "'''" in lower:
            if any(stripped_lower.startswith(qkw) or f'"{qkw}' in lower for qkw in query_starters):
                in_query_string = True
                query_start_line = i

        # Check for f-string with query keywords at START of the string value
        # Pattern: f"SELECT ... or f'SELECT ...
        if stripped_lower.startswith("f'") or stripped_lower.startswith('f"'):
            # Extract what comes after the f' or f"
            after_quote = stripped_lower[2:].lstrip()
            if any(after_quote.startswith(qkw) for qkw in query_starters):
                violations.append(
                    f"{path}:{i}: f-string in SQL/GraphQL query. Use parameterized queries."
                )

        # Check for .format() on query strings
        if in_query_string and ".format(" in line:
            violations.append(
                f"{path}:{i}: .format() in SQL/GraphQL query. Use parameterized queries."
            )

        # End of multiline string
        if in_query_string and i > query_start_line:
            if '"""' in line or "'''" in line:
                in_query_string = False

    return violations


def check_next_without_default(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check for next() calls without a default value."""
    if not cfg.ban_next_without_default:
        return []
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = get_call_name(node)
            if name == "next":
                # next() with only 1 arg (iterator) and no default
                if len(node.args) == 1 and not node.keywords:
                    violations.append(
                        f"{path}:{node.lineno}: next() without default. "
                        "Use next(iter, default) to handle empty iterators."
                    )
    return violations


def check_assert_usage(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check for assert statements (should use explicit validation)."""
    if not cfg.ban_assert:
        return []
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            violations.append(
                f"{path}:{node.lineno}: assert used for validation. "
                "Use explicit if/raise for production code."
            )
    return violations


def check_star_imports(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check for star imports."""
    if not cfg.ban_star_imports:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    return [f"{path}:{node.lineno}: Star import. Import specific names."]
    return []


def check_bare_except(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check for bare except:."""
    if not cfg.ban_bare_except:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            return [f"{path}:{node.lineno}: Bare except. Catch specific exceptions."]
    return []


def check_mutable_defaults(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check for mutable default args."""
    if not cfg.ban_mutable_defaults:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for default in node.args.defaults + node.args.kw_defaults:
                if default is None:
                    continue
                if isinstance(default, ast.List | ast.Dict | ast.Set):
                    return [
                        f"{path}:{node.lineno}: '{node.name}' has mutable default. "
                        "Use None and create inside function."
                    ]
    return []


def check_eval_exec(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check for eval/exec."""
    if not cfg.ban_eval_exec:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = get_call_name(node)
            if name in ("eval", "exec"):
                return [f"{path}:{node.lineno}: '{name}()' is dangerous."]
    return []


def check_subprocess(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check subprocess safety."""
    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = get_call_name(node)
        if not name.startswith("subprocess."):
            continue

        if cfg.ban_subprocess_shell:
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value:
                    violations.append(f"{path}:{node.lineno}: shell=True is dangerous.")

        if cfg.require_subprocess_check and name == "subprocess.run":
            has_check = any(
                kw.arg == "check" and isinstance(kw.value, ast.Constant) and kw.value.value
                for kw in node.keywords
            )
            if not has_check:
                violations.append(f"{path}:{node.lineno}: subprocess.run needs check=True.")

    return violations


def check_network_imports(path: Path, tree: ast.AST, cfg: Config) -> list[str]:
    """Check network lib imports."""
    if not cfg.blocked_network_libs or path_matches(path, cfg.network_allowed_dirs):
        return []
    for node in ast.walk(tree):
        lib = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                lib = alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            lib = node.module.split(".")[0]
        if lib and lib in cfg.blocked_network_libs:
            return [f"{path}:{node.lineno}: '{lib}' import outside allowed dirs."]
    return []


def check_function_size(
    path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, cfg: Config
) -> list[str]:
    """Function size check."""
    start = node.lineno
    end = getattr(node, "end_lineno", start)
    size = end - start + 1
    if size > cfg.max_function_lines:
        return [f"{path}:{start}: '{node.name}' is {size} lines (max {cfg.max_function_lines})."]
    return []


def check_async_zone(
    path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, cfg: Config
) -> list[str]:
    """Check sync functions in async zones."""
    if not cfg.async_only_dirs or not path_matches(path, cfg.async_only_dirs):
        return []
    if isinstance(node, ast.AsyncFunctionDef) or node.name.startswith("__"):
        return []
    if path_matches(path, cfg.sync_allowed_modules):
        return []
    allowed = {"staticmethod", "classmethod", "property"}
    if allowed & {get_decorator_name(d) for d in node.decorator_list}:
        return []
    return [f"{path}:{node.lineno}: Sync '{node.name}' in async zone. Use 'async def'."]


def check_blocking_calls(path: Path, node: ast.AsyncFunctionDef, cfg: Config) -> list[str]:
    """Check blocking calls in async."""
    violations = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = get_call_name(child)
            if name in cfg.blocking_calls:
                violations.append(f"{path}:{child.lineno}: '{name}' blocks in async '{node.name}'.")
    return violations


def check_function(
    path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef, cfg: Config
) -> list[str]:
    """All function checks."""
    v = []
    v.extend(check_function_size(path, node, cfg))
    v.extend(check_async_zone(path, node, cfg))
    if isinstance(node, ast.AsyncFunctionDef):
        v.extend(check_blocking_calls(path, node, cfg))
    return v


def check_file(path: Path, cfg: Config) -> list[str]:
    """All checks on a file."""
    if any(ex in path.parts for ex in cfg.exclude_dirs):
        return []

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")

    lines = content.splitlines()
    v: list[str] = []

    # Text checks
    v.extend(check_file_size(path, lines, cfg))
    v.extend(check_banned_markers(path, content, cfg))
    v.extend(check_mock_data(path, content, cfg))
    v.extend(check_print(path, content, cfg))
    v.extend(check_type_ignore(path, content, cfg))
    v.extend(check_any_import(path, content, cfg))
    v.extend(check_naive_datetime(path, content, cfg))
    v.extend(check_unsafe_singleton(path, content, cfg))
    v.extend(check_fstring_injection(path, content, cfg))

    # AST checks
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return v

    v.extend(check_star_imports(path, tree, cfg))
    v.extend(check_bare_except(path, tree, cfg))
    v.extend(check_mutable_defaults(path, tree, cfg))
    v.extend(check_eval_exec(path, tree, cfg))
    v.extend(check_subprocess(path, tree, cfg))
    v.extend(check_network_imports(path, tree, cfg))
    v.extend(check_next_without_default(path, tree, cfg))
    v.extend(check_assert_usage(path, tree, cfg))

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            v.extend(check_function(path, node, cfg))

    return v


def main() -> int:
    """Run guardian."""
    cfg = load_config()
    files = list(iter_py_files(cfg.src_root, cfg.exclude_dirs))

    if not files:
        print(f"guardian: No files in {cfg.src_root}")
        return 0

    violations = []
    for path in files:
        violations.extend(check_file(path, cfg))

    if violations:
        print("=" * 60)
        print("GUARDIAN")
        print("=" * 60)
        for v in sorted(set(violations)):
            print(f"  {v}")
        print("=" * 60)
        print(f"{len(set(violations))} issue(s)")
        return 1

    print(f"guardian: {len(files)} files OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

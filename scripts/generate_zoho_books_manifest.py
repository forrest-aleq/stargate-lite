#!/usr/bin/env python3
"""
Generate Zoho Books operation manifest from Zoho's OpenAPI bundle.

Usage:
  python3 scripts/generate_zoho_books_manifest.py
  python3 scripts/generate_zoho_books_manifest.py --zip /tmp/openapi-all.zip
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

DEFAULT_OPENAPI_ZIP_URL = "https://www.zoho.com/books/api/v3/openapi-all.zip"
DEFAULT_OUTPUT = Path("app/connectors/zoho_books/operations_manifest.json")

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "options", "head"}
SUCCESS_CODES = {"200", "201", "202", "203", "204", "206", "207", "208", "226", "default"}


def sanitize(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        value = "operation"
    if value[0].isdigit():
        value = f"op_{value}"
    return value


def fallback_opid(method: str, path: str) -> str:
    bits = [method.lower()] + [sanitize(part) for part in re.split(r"[^a-zA-Z0-9]+", path) if part]
    return sanitize("_".join(bits))


def deref_param(spec: dict[str, Any], param: dict[str, Any]) -> dict[str, Any]:
    if "$ref" in param:
        ref = str(param["$ref"])
        if ref.startswith("#/components/parameters/"):
            key = ref.split("/")[-1]
            return spec.get("components", {}).get("parameters", {}).get(key, {})
    return param


def extract_params(
    spec: dict[str, Any], path_item: dict[str, Any], operation: dict[str, Any]
) -> tuple[list[str], list[str]]:
    path_params: list[str] = []
    query_params: list[str] = []
    merged: list[dict[str, Any]] = []
    merged.extend(path_item.get("parameters", []))
    merged.extend(operation.get("parameters", []))
    seen: set[tuple[str, str]] = set()

    for raw in merged:
        if not isinstance(raw, dict):
            continue
        param = deref_param(spec, raw)
        name = param.get("name")
        location = param.get("in")
        if not name or not location:
            continue
        key = (str(name), str(location))
        if key in seen:
            continue
        seen.add(key)

        if location == "path":
            path_params.append(str(name))
        elif location == "query":
            query_params.append(str(name))

    return sorted(path_params), sorted(query_params)


def response_content_types(operation: dict[str, Any]) -> list[str]:
    content_types: set[str] = set()
    responses = operation.get("responses", {})
    if not isinstance(responses, dict):
        return []
    for code, response in responses.items():
        if str(code) not in SUCCESS_CODES or not isinstance(response, dict):
            continue
        content = response.get("content", {})
        if isinstance(content, dict):
            for key in content:
                content_types.add(str(key))
    return sorted(content_types)


def has_binary_response(content_types: list[str]) -> bool:
    if not content_types:
        return False
    for content_type in content_types:
        c = content_type.lower()
        if c.startswith("application/json") or c.startswith("text/json") or c.endswith("+json"):
            continue
        return True
    return False


def build_manifest(zip_path: Path) -> dict[str, Any]:
    raw_entries: list[dict[str, Any]] = []
    modules_for_scopes: set[str] = set()

    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".yml"):
                continue
            spec = yaml.safe_load(zf.read(name)) or {}
            if not isinstance(spec, dict):
                continue
            stem = Path(name).stem.replace("-", "_")
            global_security = spec.get("security", [])

            for path, path_item in (spec.get("paths", {}) or {}).items():
                if not isinstance(path_item, dict):
                    continue
                for method, operation in path_item.items():
                    if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                        continue

                    opid = sanitize(
                        operation.get("operationId") or fallback_opid(method, str(path))
                    )
                    summary = (
                        operation.get("summary")
                        or operation.get("description")
                        or f"{method.upper()} {path}"
                    )
                    description = operation.get("description") or summary
                    path_params, query_params = extract_params(spec, path_item, operation)

                    request_body = operation.get("requestBody") or {}
                    has_body = isinstance(request_body, dict) and bool(request_body)
                    body_required = bool(request_body.get("required", False)) if has_body else False
                    request_media_types = (
                        sorted((request_body.get("content") or {}).keys()) if has_body else []
                    )

                    response_types = response_content_types(operation)
                    returns_binary = has_binary_response(response_types)

                    security = []
                    if isinstance(global_security, list):
                        security.extend(global_security)
                    if isinstance(operation.get("security"), list):
                        security.extend(operation["security"])
                    for sec in security:
                        if not isinstance(sec, dict):
                            continue
                        for values in sec.values():
                            if not isinstance(values, list):
                                continue
                            for scope in values:
                                parts = str(scope).split(".")
                                if len(parts) >= 2 and parts[0] == "ZohoBooks":
                                    modules_for_scopes.add(parts[1])

                    raw_entries.append(
                        {
                            "source_file": name,
                            "source_module": stem,
                            "operation_id": opid,
                            "method": method.upper(),
                            "path": path,
                            "summary": summary,
                            "description": description,
                            "path_params": path_params,
                            "query_params": query_params,
                            "has_request_body": has_body,
                            "request_body_required": body_required,
                            "request_media_types": request_media_types,
                            "response_content_types": response_types,
                            "returns_binary": returns_binary,
                        }
                    )

    counter = Counter(entry["operation_id"] for entry in raw_entries)
    used: set[str] = set()
    operations: list[dict[str, Any]] = []

    for entry in raw_entries:
        key_suffix = entry["operation_id"]
        if counter[key_suffix] > 1:
            key_suffix = f"{key_suffix}_{sanitize(entry['source_module'])}"
        capability_key = f"zoho_books.{key_suffix}"
        if capability_key in used:
            digest = hashlib.sha256(f"{entry['method']}:{entry['path']}".encode()).hexdigest()[:8]
            capability_key = f"{capability_key}_{digest}"
        used.add(capability_key)

        operations.append(
            {
                **entry,
                "capability_key": capability_key,
                "tool_name": capability_key,
            }
        )

    operations.sort(key=lambda op: (op["source_file"], op["path"], op["method"]))
    recommended_scopes = ",".join(
        f"ZohoBooks.{module}.ALL" for module in sorted(modules_for_scopes)
    )

    return {
        "source_zip": str(zip_path),
        "operation_count": len(operations),
        "recommended_scopes": recommended_scopes,
        "operations": operations,
    }


def ensure_zip(path: Path | None) -> Path:
    if path:
        return path
    tmpdir = Path(tempfile.mkdtemp(prefix="zoho_books_openapi_"))
    target = tmpdir / "openapi-all.zip"
    urllib.request.urlretrieve(DEFAULT_OPENAPI_ZIP_URL, target)  # noqa: S310
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip",
        type=Path,
        default=None,
        help="Path to Zoho Books openapi-all.zip",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output manifest path",
    )
    args = parser.parse_args()

    zip_path = ensure_zip(args.zip)
    manifest = build_manifest(zip_path)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {args.output} with {manifest['operation_count']} operations")


if __name__ == "__main__":
    main()

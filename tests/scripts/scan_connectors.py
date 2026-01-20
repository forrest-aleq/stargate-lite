#!/usr/bin/env python3
"""
Scan all connectors and extract their public methods
to verify registry mappings
"""

import ast
from pathlib import Path


def get_class_methods(file_path: Path):
    """Extract all public methods from a connector class"""
    with file_path.open() as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return None, []

    class_name = None
    methods = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Get the main connector class (usually ends with Connector)
            if node.name.endswith("Connector") or node.name.endswith("Utility"):
                class_name = node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        # Skip private methods and __init__
                        if not item.name.startswith("_"):
                            methods.append(item.name)

    return class_name, methods


def scan_all_connectors():
    """Scan all connector files"""
    connectors_dir = Path("app/connectors")
    results = {}

    for file_path in sorted(connectors_dir.glob("*.py")):
        if file_path.name == "__init__.py":
            continue

        class_name, methods = get_class_methods(file_path)
        if class_name:
            results[file_path.stem] = {
                "file": file_path.name,
                "class": class_name,
                "methods": methods,
            }

    return results


if __name__ == "__main__":
    print("Scanning all connectors...\n")
    print("=" * 80)

    results = scan_all_connectors()

    for connector_name, info in results.items():
        print(f"\n{connector_name}.py ({info['class']})")
        print("-" * 80)
        for method in info["methods"]:
            print(f"  - {method}")

    print("\n" + "=" * 80)
    print(f"Total connectors scanned: {len(results)}")

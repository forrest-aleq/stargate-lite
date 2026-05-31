from __future__ import annotations

import sys
from collections.abc import Callable

import pytest

from scripts import release_gate


def _run_gate(
    monkeypatch: pytest.MonkeyPatch,
    *,
    mode: str,
    target_sha: str,
    main_sha: str,
    staging_sha: str,
    is_ancestor: Callable[[str, str], bool],
    tree: Callable[[str], str] | None = None,
    branch_contains_tree: Callable[[str, str], bool] | None = None,
) -> int:
    monkeypatch.setattr(release_gate, "_fetch_refs", lambda *_args: None)
    monkeypatch.setattr(
        release_gate,
        "_resolve",
        lambda ref: {
            "HEAD": target_sha,
            "origin/main": main_sha,
            "origin/staging": staging_sha,
        }[ref],
    )
    monkeypatch.setattr(release_gate, "_is_ancestor", is_ancestor)
    if tree is not None:
        monkeypatch.setattr(release_gate, "_tree", tree)
    if branch_contains_tree is not None:
        monkeypatch.setattr(release_gate, "_branch_contains_tree", branch_contains_tree)
    monkeypatch.setattr(
        sys,
        "argv",
        ["release_gate.py", "--mode", mode, "--target-ref", "HEAD", "--skip-fetch"],
    )
    return release_gate.main()


def test_promotion_requires_main_to_be_contained_in_staging(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_gate(
        monkeypatch,
        mode="promotion",
        target_sha="staging",
        main_sha="main",
        staging_sha="staging",
        is_ancestor=lambda ancestor, descendant: ancestor == descendant,
        branch_contains_tree=lambda _ref, _tree_sha: False,
    )

    assert result == 1


def test_promotion_accepts_squash_merged_main_content_in_staging_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_gate(
        monkeypatch,
        mode="promotion",
        target_sha="staging",
        main_sha="main",
        staging_sha="staging",
        is_ancestor=lambda ancestor, descendant: ancestor == descendant,
        tree=lambda ref: "main-tree" if ref == "main" else ref,
        branch_contains_tree=lambda ref, tree_sha: (
            ref == "origin/staging" and tree_sha == "main-tree"
        ),
    )

    assert result == 0


def test_production_accepts_main_merge_commit_with_staging_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def is_ancestor(ancestor: str, descendant: str) -> bool:
        return (ancestor, descendant) == ("target", "main")

    result = _run_gate(
        monkeypatch,
        mode="production",
        target_sha="target",
        main_sha="main",
        staging_sha="staging",
        is_ancestor=is_ancestor,
        tree=lambda ref: "same-tree" if ref in {"target", "staging"} else ref,
    )

    assert result == 0


def test_production_rejects_main_commit_with_unstaged_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def is_ancestor(ancestor: str, descendant: str) -> bool:
        return (ancestor, descendant) == ("target", "main")

    result = _run_gate(
        monkeypatch,
        mode="production",
        target_sha="target",
        main_sha="main",
        staging_sha="staging",
        is_ancestor=is_ancestor,
        tree=lambda ref: f"{ref}-tree",
    )

    assert result == 1

"""Tests for service-layer helpers, focused on the git-add safety fix."""

from __future__ import annotations

import subprocess
from unittest import mock

from okf_tools.service import _git_add, get_stats


class TestGitAddDoesNotHang:
    """`_git_add` must never block or raise. The MCP server runs over stdio, so
    capturing git's output via pipes can make subprocess.run hang forever on
    Windows (a child holding an inherited pipe defeats the post-timeout drain).
    These tests pin the safe invocation and best-effort behaviour.
    """

    def test_uses_devnull_not_capture(self, tmp_path):
        """Streams are redirected to DEVNULL and output is never captured."""
        with mock.patch("okf_tools.service.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            _git_add(tmp_path, tmp_path / "concept.md")

        assert run.call_count == 1
        kwargs = run.call_args.kwargs
        assert kwargs.get("stdin") is subprocess.DEVNULL
        assert kwargs.get("stdout") is subprocess.DEVNULL
        assert kwargs.get("stderr") is subprocess.DEVNULL
        # capture_output would re-introduce the blocking pipes.
        assert "capture_output" not in kwargs
        assert kwargs.get("timeout")  # a timeout must be set

    def test_timeout_is_swallowed(self, tmp_path):
        """A git that times out must not propagate an exception."""
        with mock.patch(
            "okf_tools.service.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="git add", timeout=5),
        ):
            _git_add(tmp_path, tmp_path / "concept.md")  # must not raise

    def test_missing_git_is_swallowed(self, tmp_path):
        """A missing git binary must not propagate an exception."""
        with mock.patch(
            "okf_tools.service.subprocess.run", side_effect=FileNotFoundError()
        ):
            _git_add(tmp_path, tmp_path / "concept.md")  # must not raise

    def test_nonzero_exit_does_not_raise(self, tmp_path):
        """A non-git directory (git add returns non-zero) must not raise."""
        # Real invocation against a temp dir that is not a git repo.
        _git_add(tmp_path, tmp_path / "concept.md")  # must return cleanly

class TestGetStatsToleratesNullTags:
    """`get_stats` must survive a concept whose `tags` key is present but null.

    `tags: null` is valid YAML and parses to None, not to an empty list. Iterating
    it directly raised TypeError and took the whole call down, so a single such
    note made bundle statistics unavailable entirely.
    """

    def test_null_tags_does_not_raise(self, sample_config):
        concept = sample_config.bundle_path / "null-tags.md"
        concept.write_text(
            "---\ntype: Pattern\ntitle: Null tags\ntags: null\n---\n\nBody.\n",
            encoding="utf-8",
        )

        stats = get_stats(sample_config)  # must not raise

        assert stats["concept_count"] == 1
        assert stats["tag_distribution"] == {}
        assert stats["type_distribution"] == {"Pattern": 1}


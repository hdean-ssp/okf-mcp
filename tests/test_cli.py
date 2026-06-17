"""Tests for cli.py: input parsing, output formatting, and format detection."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from okf_tools.cli import (
    _detect_format,
    _handle_error,
    _output,
    _parse_commit_input,
    _parse_update_input,
    _print_dict,
    okf,
)


# ---------------------------------------------------------------------------
# _detect_format
# ---------------------------------------------------------------------------


class TestDetectFormat:
    def test_explicit_json(self):
        assert _detect_format("json") == "json"

    def test_explicit_text(self):
        assert _detect_format("text") == "text"

    def test_explicit_brief(self):
        assert _detect_format("brief") == "brief"

    def test_none_tty_returns_text(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            assert _detect_format(None) == "text"

    def test_none_pipe_returns_json(self):
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            assert _detect_format(None) == "json"


# ---------------------------------------------------------------------------
# _parse_commit_input
# ---------------------------------------------------------------------------


class TestParseCommitInput:
    def test_json_input(self):
        kwargs = {
            "json_input": '{"title": "Test", "type": "Pattern", "content": "Body"}',
            "file_input": None,
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
            "target_path": None,
            "check_duplicates": False,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result == {"title": "Test", "type": "Pattern", "content": "Body"}

    def test_file_input(self, tmp_path):
        json_file = tmp_path / "input.json"
        json_file.write_text('{"title": "From File", "type": "Decision", "content": "File body"}')
        kwargs = {
            "json_input": None,
            "file_input": str(json_file),
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
            "target_path": None,
            "check_duplicates": False,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result["title"] == "From File"
        assert result["type"] == "Decision"

    def test_individual_flags(self):
        kwargs = {
            "json_input": None,
            "file_input": None,
            "title": "Flag Title",
            "content": "Flag Content",
            "concept_type": "Runbook",
            "tags": "alpha, beta, gamma",
            "target_path": None,
            "check_duplicates": False,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result["title"] == "Flag Title"
        assert result["content"] == "Flag Content"
        assert result["type"] == "Runbook"
        assert result["tags"] == ["alpha", "beta", "gamma"]

    def test_tags_stripped(self):
        kwargs = {
            "json_input": None,
            "file_input": None,
            "title": "T",
            "content": "C",
            "concept_type": "P",
            "tags": "  spaces , around , tags  ",
            "target_path": None,
            "check_duplicates": False,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result["tags"] == ["spaces", "around", "tags"]

    def test_target_path_added(self):
        kwargs = {
            "json_input": '{"title": "X", "type": "Y", "content": "Z"}',
            "file_input": None,
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
            "target_path": "subdir/nested",
            "check_duplicates": False,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result["path"] == "subdir/nested"

    def test_check_duplicates_flag(self):
        kwargs = {
            "json_input": '{"title": "X", "type": "Y", "content": "Z"}',
            "file_input": None,
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
            "target_path": None,
            "check_duplicates": True,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result["check_duplicates"] is True

    def test_force_flag(self):
        kwargs = {
            "json_input": '{"title": "X", "type": "Y", "content": "Z"}',
            "file_input": None,
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
            "target_path": None,
            "check_duplicates": False,
            "force": True,
        }
        result = _parse_commit_input(kwargs)
        assert result["force"] is True

    def test_json_takes_precedence_over_flags(self):
        """When --json is provided, individual flags are ignored for data."""
        kwargs = {
            "json_input": '{"title": "JSON Title", "type": "P", "content": "C"}',
            "file_input": None,
            "title": "Flag Title",
            "content": "Flag Content",
            "concept_type": "Decision",
            "tags": "a,b",
            "target_path": None,
            "check_duplicates": False,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result["title"] == "JSON Title"
        assert "Flag Title" not in str(result)

    def test_empty_flags_produce_empty_dict(self):
        kwargs = {
            "json_input": None,
            "file_input": None,
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
            "target_path": None,
            "check_duplicates": False,
            "force": False,
        }
        result = _parse_commit_input(kwargs)
        assert result == {}


# ---------------------------------------------------------------------------
# _parse_update_input
# ---------------------------------------------------------------------------


class TestParseUpdateInput:
    def test_json_input(self):
        kwargs = {
            "json_input": '{"title": "Updated", "tags": ["new"]}',
            "file_input": None,
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
        }
        result = _parse_update_input(kwargs)
        assert result == {"title": "Updated", "tags": ["new"]}

    def test_file_input(self, tmp_path):
        json_file = tmp_path / "update.json"
        json_file.write_text('{"content": "New body"}')
        kwargs = {
            "json_input": None,
            "file_input": str(json_file),
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
        }
        result = _parse_update_input(kwargs)
        assert result == {"content": "New body"}

    def test_individual_flags(self):
        kwargs = {
            "json_input": None,
            "file_input": None,
            "title": "New Title",
            "content": "New Content",
            "concept_type": "Decision",
            "tags": "x, y",
        }
        result = _parse_update_input(kwargs)
        assert result["title"] == "New Title"
        assert result["content"] == "New Content"
        assert result["type"] == "Decision"
        assert result["tags"] == ["x", "y"]

    def test_partial_flags(self):
        """Only provided flags are included."""
        kwargs = {
            "json_input": None,
            "file_input": None,
            "title": "Only Title",
            "content": None,
            "concept_type": None,
            "tags": None,
        }
        result = _parse_update_input(kwargs)
        assert result == {"title": "Only Title"}

    def test_empty_produces_empty_dict(self):
        kwargs = {
            "json_input": None,
            "file_input": None,
            "title": None,
            "content": None,
            "concept_type": None,
            "tags": None,
        }
        result = _parse_update_input(kwargs)
        assert result == {}


# ---------------------------------------------------------------------------
# _output formatting
# ---------------------------------------------------------------------------


class TestOutput:
    def _make_ctx(self, fmt: str) -> click.Context:
        """Create a Click context with the given format."""
        ctx = click.Context(okf)
        ctx.ensure_object(dict)
        ctx.obj["format"] = fmt
        return ctx

    def test_json_format_dict(self):
        ctx = self._make_ctx("json")
        with ctx.scope():
            with patch("click.echo") as mock_echo:
                _output(ctx, {"key": "value"})
                output = mock_echo.call_args[0][0]
                data = json.loads(output)
                assert data == {"key": "value"}

    def test_json_format_list(self):
        ctx = self._make_ctx("json")
        with ctx.scope():
            with patch("click.echo") as mock_echo:
                _output(ctx, [{"a": 1}, {"b": 2}])
                output = mock_echo.call_args[0][0]
                data = json.loads(output)
                assert data == [{"a": 1}, {"b": 2}]

    def test_brief_format_list(self):
        ctx = self._make_ctx("brief")
        with ctx.scope():
            with patch("click.echo") as mock_echo:
                _output(ctx, [
                    {"concept_id": "patterns/retry", "title": "Retry Pattern"},
                    {"concept_id": "decisions/cache", "title": "Cache Decision"},
                ])
                calls = [c[0][0] for c in mock_echo.call_args_list]
                assert "patterns/retry\tRetry Pattern" in calls
                assert "decisions/cache\tCache Decision" in calls

    def test_brief_format_empty_list(self):
        ctx = self._make_ctx("brief")
        with ctx.scope():
            with patch("click.echo") as mock_echo:
                _output(ctx, [])
                mock_echo.assert_called_once_with("No matching concepts.", err=True)

    def test_text_format_dict(self):
        ctx = self._make_ctx("text")
        with ctx.scope():
            with patch("click.echo") as mock_echo:
                _output(ctx, {"concept_id": "test", "title": "Test"})
                calls = [c[0][0] for c in mock_echo.call_args_list]
                assert "concept_id: test" in calls
                assert "title: Test" in calls

    def test_text_format_empty_list(self):
        ctx = self._make_ctx("text")
        with ctx.scope():
            with patch("click.echo") as mock_echo:
                _output(ctx, [])
                mock_echo.assert_called_once_with("No matching concepts.", err=True)

    def test_text_format_scalar(self):
        ctx = self._make_ctx("text")
        with ctx.scope():
            with patch("click.echo") as mock_echo:
                _output(ctx, "plain string")
                mock_echo.assert_called_once_with("plain string")


# ---------------------------------------------------------------------------
# _print_dict
# ---------------------------------------------------------------------------


class TestPrintDict:
    def test_flat_dict(self):
        with patch("click.echo") as mock_echo:
            _print_dict({"a": 1, "b": "hello"})
            calls = [c[0][0] for c in mock_echo.call_args_list]
            assert "a: 1" in calls
            assert "b: hello" in calls

    def test_nested_dict(self):
        with patch("click.echo") as mock_echo:
            _print_dict({"outer": {"inner_a": 1, "inner_b": 2}})
            calls = [c[0][0] for c in mock_echo.call_args_list]
            assert "outer:" in calls
            assert "  inner_a: 1" in calls
            assert "  inner_b: 2" in calls

    def test_long_list_collapsed(self):
        with patch("click.echo") as mock_echo:
            _print_dict({"items": [1, 2, 3, 4, 5]})
            calls = [c[0][0] for c in mock_echo.call_args_list]
            assert "items: [5 items]" in calls

    def test_short_list_shown(self):
        with patch("click.echo") as mock_echo:
            _print_dict({"tags": ["a", "b", "c"]})
            calls = [c[0][0] for c in mock_echo.call_args_list]
            assert "tags: ['a', 'b', 'c']" in calls


# ---------------------------------------------------------------------------
# _handle_error
# ---------------------------------------------------------------------------


class TestHandleError:
    def test_text_format(self):
        runner = CliRunner()

        @click.command()
        @click.pass_context
        def dummy(ctx):
            ctx.ensure_object(dict)
            ctx.obj["format"] = "text"
            _handle_error(ctx, "Something went wrong", exit_code=1)

        result = runner.invoke(dummy)
        assert result.exit_code == 1
        assert "error: Something went wrong" in result.output

    def test_json_format(self):
        runner = CliRunner()

        @click.command()
        @click.pass_context
        def dummy(ctx):
            ctx.ensure_object(dict)
            ctx.obj["format"] = "json"
            _handle_error(ctx, "Something broke", exit_code=2)

        result = runner.invoke(dummy)
        assert result.exit_code == 2
        # JSON error goes to stderr, captured in result.output by CliRunner
        assert "Something broke" in result.output


# ---------------------------------------------------------------------------
# Integration: CLI runner tests
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    def test_version_flag(self):
        runner = CliRunner()
        result = runner.invoke(okf, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output
        assert "OKF spec v0.1" in result.output

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(okf, ["--help"])
        assert result.exit_code == 0
        assert "OKF bundle tools" in result.output

    def test_init_creates_bundle(self, tmp_path, monkeypatch):
        """okf init in a directory creates the .okf structure."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(okf, ["init"])
        assert result.exit_code == 0
        assert (tmp_path / ".okf" / "config.json").exists()

    def test_init_already_initialised(self, tmp_path, monkeypatch):
        """okf init in an existing bundle reports error."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        runner.invoke(okf, ["init"])
        result = runner.invoke(okf, ["init"])
        assert result.exit_code == 1
        assert "already" in result.output.lower()

    @patch("okf_tools.service.embed_text", return_value=[0.1] * 384)
    @patch("okf_tools.service.VectorIndex")
    def test_commit_with_json(self, mock_idx_cls, mock_embed, tmp_path, monkeypatch):
        """okf commit --json creates a concept."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        runner.invoke(okf, ["init"])

        mock_idx = mock_idx_cls.return_value
        mock_idx.search.return_value = []
        mock_idx.close.return_value = None
        mock_idx.upsert.return_value = None

        input_json = json.dumps({
            "title": "CLI Test",
            "type": "Pattern",
            "content": "CLI body content",
        })
        result = runner.invoke(okf, ["commit", "--json", input_json])
        assert result.exit_code == 0
        assert "concept_id" in result.output

    @patch("okf_tools.service.embed_text", return_value=[0.1] * 384)
    @patch("okf_tools.service.VectorIndex")
    def test_commit_dry_run(self, mock_idx_cls, mock_embed, tmp_path, monkeypatch):
        """okf commit --dry-run shows what would happen without writing."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        runner.invoke(okf, ["init"])

        input_json = json.dumps({
            "title": "Dry Run Test",
            "type": "Pattern",
            "content": "Should not be written",
        })
        result = runner.invoke(okf, ["commit", "--json", input_json, "--dry-run"])
        assert result.exit_code == 0
        assert "dry_run" in result.output.lower() or "Dry Run Test" in result.output
        # No file should be created
        md_files = list(tmp_path.rglob("*.md"))
        concept_files = [f for f in md_files if f.name not in ("index.md", "log.md")]
        assert concept_files == []

    def test_fetch_empty_query(self, tmp_path, monkeypatch):
        """okf fetch with empty query reports error."""
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        # fetch requires a query argument, Click will error on missing arg
        result = runner.invoke(okf, ["fetch", ""])
        # Empty string query should produce an error
        assert result.exit_code != 0 or "non-empty" in result.output.lower() or "error" in result.output.lower()

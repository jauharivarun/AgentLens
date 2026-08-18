import ast

from app.agent.tools import (
    normalize_written_content,
    preview_csv,
    run_command,
    run_tests,
    summarize_test_failure,
)
from app.gateway.adapters.groq_adapter import GroqAdapter


def test_blocked_command_is_rejected():
    try:
        run_command("rm -rf /")
        assert False, "expected PermissionError"
    except PermissionError:
        pass


def test_preview_csv_returns_headers_and_rows():
    result = preview_csv("data/sales.csv", rows=3)
    assert result["path"] == "data/sales.csv"
    assert result["headers"]
    assert len(result["rows"]) == 3
    assert result["row_count"] >= 3


def test_preview_csv_resolves_bare_filename():
    result = preview_csv("sales.csv", rows=3)
    assert result["path"] == "data/sales.csv"
    assert len(result["rows"]) == 3


def test_preview_csv_missing_file_lists_alternatives():
    try:
        preview_csv("nope.csv")
        assert False, "expected FileNotFoundError"
    except FileNotFoundError as exc:
        assert "data/sales.csv" in str(exc)


def test_preview_csv_rejects_non_csv():
    try:
        preview_csv("src/report.py")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_run_tests_rejects_path_outside_workspace():
    try:
        run_tests("../secret")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_double_escaped_python_is_recovered():
    escaped = "import re\\n\\n\\ndef slug(text):\\n    return text.lower()"
    content, decoded = normalize_written_content(escaped, ".py")
    assert decoded is True
    assert len(content.splitlines()) == 5
    ast.parse(content)


def test_legitimate_python_one_liner_is_not_rewritten():
    source = 'print("a\\nb")'
    content, decoded = normalize_written_content(source, ".py")
    assert decoded is False
    assert content == source


def test_normal_multiline_content_is_untouched():
    source = "def f():\n    return 1\n"
    content, decoded = normalize_written_content(source, ".py")
    assert decoded is False
    assert content == source


def test_unparseable_content_is_left_for_the_model():
    content, decoded = normalize_written_content("def (:\\n  ??", ".py")
    assert decoded is False


def test_failure_summary_only_for_nonzero_exit():
    assert summarize_test_failure({"exit_code": 0, "stdout": "1 passed", "stderr": ""}) is None
    summary = summarize_test_failure({"exit_code": 2, "stdout": "collected 0", "stderr": "SyntaxError"})
    assert "SyntaxError" in summary


def test_groq_adapter_requires_key():
    import asyncio

    result = asyncio.run(GroqAdapter(api_key="").generate(model="llama-3.1-8b-instant", messages=[], tools=None))
    assert result.status == "failed"
    assert result.error_type == "ProviderNotConfigured"

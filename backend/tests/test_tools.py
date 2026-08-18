from app.agent.tools import preview_csv, run_command, run_tests
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


def test_groq_adapter_requires_key():
    import asyncio

    result = asyncio.run(GroqAdapter(api_key="").generate(model="llama-3.1-8b-instant", messages=[], tools=None))
    assert result.status == "failed"
    assert result.error_type == "ProviderNotConfigured"

from app.agent.tools import line_diff, list_files, resolve_workspace_path, write_file
from app.telemetry.analytics import overview
from app.telemetry.memory import memory_store
from app.telemetry.recorder import TelemetryRecorder


def test_workspace_list_includes_sample_files():
    result = list_files()
    assert result["count"] > 0
    assert any(path.endswith("sales.csv") for path in result["files"])


def test_line_diff_counts_additions_and_removals():
    added, removed = line_diff("a\nb\nc\n", "a\nx\nc\n")
    assert added == 1
    assert removed == 1


def test_write_file_stays_inside_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_PATH", str(tmp_path))
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        result = write_file("notes.txt", "hello")
        assert result["path"] == "notes.txt"
        assert (tmp_path / "notes.txt").read_text() == "hello"
        try:
            resolve_workspace_path("../secret.txt")
            raised = False
        except ValueError:
            raised = True
        assert raised
    finally:
        get_settings.cache_clear()


def test_overview_sums_tokens_from_events():
    store = memory_store
    store.executions.clear()
    store.llm_events.clear()
    installation = "inst-test"
    store.executions["e1"] = {
        "id": "e1",
        "installation_id": installation,
        "started_at": "2026-01-01T00:00:00+00:00",
        "provider": "openai",
        "model_id": "gpt-4o-mini",
        "llm_call_count": 1,
        "tool_call_count": 0,
        "retry_count": 0,
        "duration_ms": 1000,
        "outcome": "success",
        "status": "completed",
        "task_id": None,
    }
    store.llm_events.append(
        {
            "execution_id": "e1",
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
            "estimated_cost_usd": 0.01,
            "usage_available": True,
        }
    )
    result = overview(installation, {})
    assert result["total_tokens"] == 1500
    assert result["executions"] == 1
    assert result["llm_calls"] == 1


def test_history_includes_prompt_and_answer():
    from app.telemetry.analytics import history

    store = memory_store
    store.executions.clear()
    store.tasks.clear()
    store.executions["e2"] = {
        "id": "e2",
        "installation_id": "inst-history",
        "started_at": "2026-01-01T00:00:00+00:00",
        "provider": "groq",
        "model_id": "openai/gpt-oss-20b",
        "task_id": "t2",
        "task_text": "Summarize sales.csv",
        "final_output": "North region led revenue.",
        "status": "completed",
        "outcome": "success",
        "llm_call_count": 1,
        "tool_call_count": 0,
        "retry_count": 0,
    }
    store.tasks["t2"] = {"id": "t2", "task_text": "Summarize sales.csv", "rag_enabled": False}
    rows = history("inst-history", {})
    assert rows[0]["task_text"] == "Summarize sales.csv"
    assert rows[0]["final_output"] == "North region led revenue."
    assert rows[0]["model"] == "Groq / GPT-OSS 20B"


def test_groq_model_label_hides_openai_slug():
    from app.catalog import model_label

    assert model_label("groq", "openai/gpt-oss-20b") == "Groq / GPT-OSS 20B"
    assert model_label("openai", "gpt-4o-mini") == "OpenAI / GPT-4o mini"


def test_stop_execution_marks_cancelled():
    import asyncio

    rec = TelemetryRecorder()

    async def _run():
        execution = await rec.start_execution(
            installation_id="abc",
            workspace_id="demo-workspace",
            task_text="hello",
            task_type="general",
            rag_enabled=False,
            comparison_group_id=None,
            provider="openai",
            model_id="gpt-4o-mini",
        )
        stopped = await rec.stop_execution(execution["id"], "Stopped by user.")
        assert stopped is not None
        assert stopped["status"] == "cancelled"
        assert stopped["outcome"] == "cancelled"
        completed = await rec.complete_execution(execution["id"], "should not overwrite")
        assert completed["status"] == "cancelled"

    asyncio.run(_run())


def test_recorder_does_not_crash_without_supabase():
    import asyncio

    rec = TelemetryRecorder()

    async def _run():
        execution = await rec.start_execution(
            installation_id="abc",
            workspace_id="demo-workspace",
            task_text="hello",
            task_type="general",
            rag_enabled=False,
            comparison_group_id=None,
            provider="openai",
            model_id="gpt-4o-mini",
        )
        assert execution["status"] == "running"
        completed = await rec.complete_execution(execution["id"], "done")
        assert completed is not None
        assert completed["status"] == "completed"

    asyncio.run(_run())


def test_store_falls_back_to_memory_without_supabase(monkeypatch):
    """A clone with no Supabase credentials must behave exactly as before."""
    from app.telemetry import store, supabase_store
    from app.telemetry.memory import memory_store

    monkeypatch.setattr(supabase_store, "get_supabase", lambda: None)
    memory_store.insert_execution(
        {"id": "fallback-exec", "installation_id": "fallback-install", "started_at": "2026-01-01T00:00:00+00:00", "task_id": "fallback-task"}
    )
    memory_store.insert_task({"id": "fallback-task", "task_text": "local", "task_type": "general"})
    memory_store.append_llm({"id": "fallback-llm", "execution_id": "fallback-exec", "total_tokens": 15})

    assert [row["id"] for row in store.list_executions("fallback-install")] == ["fallback-exec"]
    assert len(store.llm_for("fallback-exec")) == 1
    assert store.llm_for_many(["fallback-exec"])["fallback-exec"][0]["id"] == "fallback-llm"
    assert store.get_task("fallback-task")["task_text"] == "local"
    assert store.get_execution("fallback-exec") is not None


def test_completion_persists_live_counters():
    """Counters accumulate on the memory row; the Supabase patch must carry them too."""
    from app.telemetry.recorder import _summary_patch

    execution = {"llm_call_count": 3, "tool_call_count": 7, "estimated_cost_usd": 0.0042, "lines_added": 12}
    patch = _summary_patch(execution)
    assert patch["llm_call_count"] == 3
    assert patch["tool_call_count"] == 7
    assert patch["estimated_cost_usd"] == 0.0042
    assert patch["lines_added"] == 12
    assert "status" not in patch

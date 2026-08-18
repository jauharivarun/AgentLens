import { useEffect, useState } from "react";
import { api } from "../api/client";

export type ViewedFile = { name: string; path: string; bytes: number };

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function downloadText(name: string, content: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function FileViewer({ file, onClose }: { file: ViewedFile; onClose: () => void }) {
  const [content, setContent] = useState<string | null>(null);
  const [truncated, setTruncated] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setContent(null);
    setError(null);
    api
      .fileContent(file.path)
      .then((data) => {
        if (cancelled) return;
        setContent(data.content);
        setTruncated(data.truncated);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Could not read this file");
      });
    return () => {
      cancelled = true;
    };
  }, [file.path]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-xl border border-[var(--border)] bg-[var(--panel)] shadow-lg">
        <div className="flex items-start justify-between gap-3 border-b border-[var(--border)] px-4 py-3">
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-white" title={file.name}>
              {file.name}
            </div>
            <div className="mono truncate text-[11px] text-[var(--muted)]" title={file.path}>
              {file.path} · {formatBytes(file.bytes)}
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              disabled={content === null}
              onClick={() => content !== null && downloadText(file.name, content)}
              className="rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-1.5 text-xs text-white hover:border-[var(--accent)] disabled:opacity-40"
            >
              Download
            </button>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-1.5 text-xs text-[var(--muted)] hover:text-white"
            >
              Close
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-auto p-4">
          {error ? (
            <p className="text-xs text-[var(--error)]">{error}</p>
          ) : content === null ? (
            <p className="text-xs text-[var(--muted)]">Loading…</p>
          ) : (
            <pre className="mono whitespace-pre-wrap break-words text-xs text-[var(--text)]">{content}</pre>
          )}
          {truncated ? (
            <p className="mt-3 text-[11px] text-[var(--warning)]">
              Preview truncated. Download the file to read all of it.
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}

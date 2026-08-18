import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

export type KnowledgeFile = { name: string; path: string; bytes: number };

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function KnowledgeFilesPanel({
  uploads,
  builtin,
  onChange,
  onError,
}: {
  uploads: KnowledgeFile[];
  builtin: KnowledgeFile[];
  onChange: (next: { uploads: KnowledgeFile[]; builtin: KnowledgeFile[] }) => void;
  onError: (message: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointer(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [open]);

  async function onDelete(name: string) {
    setDeleting(name);
    try {
      await api.deleteUpload(name);
      const listed = await api.uploads();
      onChange({
        uploads: listed.uploads || listed.files,
        builtin: listed.builtin || [],
      });
    } catch (err) {
      onError(err instanceof Error ? err.message : "Could not delete file");
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="rounded-md border border-[var(--border)] bg-[var(--bg)] px-3 py-1.5 text-xs text-white hover:border-[var(--accent)]"
      >
        Knowledge files
      </button>
      {open ? (
        <div className="absolute bottom-full left-0 z-20 mb-2 w-80 rounded-xl border border-[var(--border)] bg-[var(--panel)] p-3 shadow-lg">
          <div className="text-xs font-medium text-white">Indexed for Search knowledge</div>
          <p className="mt-1 text-[11px] text-[var(--muted)]">
            Delete an upload so it is not retrieved on the next run. Built-in demo files stay.
          </p>
          <div className="mt-3 text-[11px] uppercase tracking-wide text-[var(--muted)]">Your uploads</div>
          {uploads.length ? (
            <ul className="mt-1 space-y-1">
              {uploads.map((file) => (
                <li key={file.path} className="flex items-center gap-2 rounded-md border border-[var(--border)] bg-[var(--bg)] px-2 py-1.5">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs text-white" title={file.name}>
                      {file.name}
                    </div>
                    <div className="text-[11px] text-[var(--muted)]">{formatBytes(file.bytes)}</div>
                  </div>
                  <button
                    type="button"
                    disabled={deleting === file.name}
                    onClick={() => onDelete(file.name)}
                    className="shrink-0 text-xs text-[var(--error)] hover:text-white disabled:opacity-40"
                  >
                    {deleting === file.name ? "Deleting…" : "Delete"}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-xs text-[var(--muted)]">No uploads yet.</p>
          )}
          <div className="mt-3 text-[11px] uppercase tracking-wide text-[var(--muted)]">Built-in knowledge</div>
          <p className="mt-1 text-[11px] text-[var(--muted)]">Always included when Search knowledge is on.</p>
          <ul className="mt-1 space-y-1">
            {builtin.map((file) => (
              <li key={file.path} className="truncate text-xs text-[var(--muted)]" title={file.path}>
                {file.name}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

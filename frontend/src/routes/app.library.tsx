import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Paper } from "@/lib/api";
import { useAtlassUser } from "@/lib/atlass-store";
import { AppShell } from "@/components/atlass/AppShell";
import { StatusChip, statusToVariant, humanStatus } from "@/components/atlass/StatusChip";
import { EmptyState } from "@/components/atlass/EmptyState";
import { ErrorState } from "@/components/atlass/ErrorState";
import { Skeleton } from "@/components/atlass/Skeleton";
import { PipelineLoading } from "@/components/atlass/Skeleton";
import { ArrowRight, Sparkles, Upload, FileText, Plus, X } from "lucide-react";

export const Route = createFileRoute("/app/library")({
  component: LibraryPage,
  head: () => ({ meta: [{ title: "Library — ATLASS" }] }),
});

function LibraryPage() {
  const { user, signIn } = useAtlassUser();
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [addOpen, setAddOpen] = useState(false);

  const userId = user?.id;
  const papers = useQuery({
    queryKey: ["papers", userId],
    queryFn: () => api.papers.list(userId!),
    enabled: !!userId,
    retry: false,
  });

  const demo = useMutation({
    mutationFn: async () => {
      const u = user ?? (await signIn());
      if (!u) throw new Error("Open the ATLASS workspace before loading a demo paper.");
      return api.papers.demo(u.id);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["papers", userId] }),
  });

  const ingest = useMutation({
    mutationFn: async (v: { source_type: "arxiv" | "doi"; source_ref: string }) => {
      const u = user ?? (await signIn());
      if (!u) throw new Error("Open the ATLASS workspace before importing a paper.");
      return api.papers.create(u.id, v);
    },
    onSuccess: () => {
      setAddOpen(false);
      qc.invalidateQueries({ queryKey: ["papers", userId] });
    },
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const u = user ?? (await signIn());
      if (!u) throw new Error("Open the ATLASS workspace before uploading a paper.");
      return api.papers.upload(u.id, file);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["papers", userId] }),
  });

  const filtered =
    papers.data?.filter((p) => !q || p.title?.toLowerCase().includes(q.toLowerCase())) ?? [];

  return (
    <AppShell>
      <div className="mx-auto max-w-[1240px] px-6 py-10 sm:px-10">
        {/* Header */}
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="label-eyebrow">Library</div>
            <h1 className="mt-2 text-display text-4xl">Research corpus</h1>
            <p className="mt-2 max-w-lg text-[14px] text-muted-foreground">
              Every paper you've ingested, with pipeline status and knowledge coverage.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => demo.mutate()}
              disabled={demo.isPending}
              className="inline-flex h-9 items-center gap-1.5 rounded-md border border-hairline-strong bg-surface px-3 text-[13px] font-medium text-foreground transition hover:bg-surface-2 disabled:opacity-60"
            >
              <Sparkles className="size-3.5 text-[color:var(--evidence)]" />
              {demo.isPending ? "Loading demo…" : "Load synthetic demo"}
            </button>
            <label className="inline-flex h-9 cursor-pointer items-center gap-1.5 rounded-md border border-hairline-strong bg-surface px-3 text-[13px] font-medium text-foreground transition hover:bg-surface-2">
              <Upload className="size-3.5" /> Upload PDF
              <input
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) upload.mutate(f);
                }}
              />
            </label>
            <button
              onClick={() => setAddOpen(true)}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-3 text-[13px] font-medium text-primary-foreground transition hover:opacity-90"
            >
              <Plus className="size-3.5" /> Ingest from arXiv
            </button>
          </div>
        </div>

        {/* Filter */}
        <div className="mt-8 flex items-center gap-3">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Filter by title…"
            className="h-9 w-full max-w-sm rounded-md border border-hairline bg-surface px-3 text-[13px] text-foreground placeholder:text-muted-foreground focus:border-hairline-strong focus:outline-none"
          />
          <span className="text-mono text-[11px] text-muted-foreground">
            {papers.data?.length ?? 0} papers
          </span>
          {(demo.isPending || upload.isPending || ingest.isPending) && (
            <PipelineLoading
              label={
                upload.isPending
                  ? "Uploading PDF…"
                  : demo.isPending
                    ? "Instantiating synthetic fixture…"
                    : "Fetching source metadata…"
              }
            />
          )}
        </div>

        {/* Table */}
        <div className="mt-6 overflow-hidden rounded-xl border border-hairline bg-surface">
          <div className="hidden grid-cols-[1.6fr_120px_160px_140px_120px] gap-4 border-b border-hairline bg-surface-2/60 px-5 py-3 text-[10px] uppercase tracking-[0.14em] text-muted-foreground md:grid">
            <div>Title</div>
            <div>Source</div>
            <div>Status</div>
            <div>Coverage</div>
            <div className="text-right">Ingested</div>
          </div>

          {papers.isLoading ? (
            <div className="divide-y divide-hairline">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4 px-5 py-4">
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                </div>
              ))}
            </div>
          ) : papers.isError ? (
            <div className="p-6">
              <ErrorState
                title="Could not reach ATLASS backend"
                description={
                  <>
                    Verify the backend is running at{" "}
                    <span className="text-mono text-foreground/90">{api.base}</span>.
                  </>
                }
                onRetry={() => papers.refetch()}
              />
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              glyph="grid"
              title="Your library is empty"
              description="Ingest a paper from arXiv, upload a PDF, or load the synthetic demo to explore the full workflow."
              action={
                <button
                  onClick={() => demo.mutate()}
                  className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground hover:opacity-90"
                >
                  <Sparkles className="size-3.5" /> Load synthetic demo
                </button>
              }
            />
          ) : (
            <ul className="divide-y divide-hairline">
              {filtered.map((p) => (
                <PaperRow key={p.id} paper={p} />
              ))}
            </ul>
          )}
        </div>
      </div>

      {addOpen && (
        <IngestDialog
          onClose={() => setAddOpen(false)}
          onSubmit={(v) => ingest.mutate(v)}
          pending={ingest.isPending}
          error={ingest.error?.message}
        />
      )}
    </AppShell>
  );
}

function PaperRow({ paper }: { paper: Paper }) {
  return (
    <li className="group grid grid-cols-1 gap-2 px-5 py-4 transition hover:bg-surface-2/50 md:grid-cols-[1.6fr_120px_160px_140px_120px] md:items-center md:gap-4">
      <Link
        to="/app/paper/$paperId"
        params={{ paperId: paper.id }}
        className="min-w-0 truncate text-[14px] font-medium text-foreground transition group-hover:text-foreground"
      >
        <div className="flex items-center gap-2">
          <FileText className="size-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">{paper.title}</span>
          {paper.is_demo && (
            <span className="rounded-full border border-[color:var(--warning)]/25 bg-[color:var(--warning-soft)] px-1.5 py-[1px] text-[10px] text-[color:var(--warning)]">
              Demo fixture
            </span>
          )}
        </div>
        <div className="mt-1 truncate text-[11px] text-subtle md:hidden">
          {paper.source_type} · {humanStatus(paper.status)}
        </div>
      </Link>
      <div className="hidden text-mono text-[11px] uppercase tracking-wide text-muted-foreground md:block">
        {paper.source_type ?? "—"}
      </div>
      <div className="hidden md:block">
        <StatusChip variant={statusToVariant(paper.status)}>
          {humanStatus(paper.status)}
        </StatusChip>
      </div>
      <div className="hidden md:block">
        {paper.knowledge_coverage != null ? (
          <div className="flex items-center gap-2">
            <div className="h-1 flex-1 overflow-hidden rounded-full bg-surface-3">
              <div
                className="h-full bg-[color:var(--evidence)]"
                style={{ width: `${Math.round(paper.knowledge_coverage * 100)}%` }}
              />
            </div>
            <span className="text-mono text-[11px] text-muted-foreground">
              {Math.round(paper.knowledge_coverage * 100)}%
            </span>
          </div>
        ) : (
          <span className="text-mono text-[11px] text-subtle">—</span>
        )}
      </div>
      <div className="hidden text-right text-mono text-[11px] text-muted-foreground md:block">
        {paper.created_at ? new Date(paper.created_at).toLocaleDateString() : "—"}
      </div>
    </li>
  );
}

function IngestDialog({
  onClose,
  onSubmit,
  pending,
  error,
}: {
  onClose: () => void;
  onSubmit: (v: { source_type: "arxiv" | "doi"; source_ref: string }) => void;
  pending?: boolean;
  error?: string;
}) {
  const [type, setType] = useState<"arxiv" | "doi">("arxiv");
  const [ref, setRef] = useState("");
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4" onClick={onClose}>
      <div className="absolute inset-0 bg-background/70 backdrop-blur-md" />
      <div
        className="relative w-full max-w-md overflow-hidden rounded-xl border border-hairline-strong bg-surface shadow-[var(--shadow-float)] animate-fade-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-hairline px-5 py-4">
          <div>
            <div className="label-eyebrow">Ingest source</div>
            <h3 className="mt-1 text-[16px] font-medium text-foreground">Add a paper</h3>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="size-4" />
          </button>
        </div>
        <div className="space-y-4 p-5">
          <div className="grid grid-cols-2 gap-1 rounded-md border border-hairline bg-surface-2 p-0.5">
            {(["arxiv", "doi"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`h-7 rounded-md text-[12px] font-medium transition ${
                  type === t
                    ? "bg-background text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {t.toUpperCase()}
              </button>
            ))}
          </div>
          <div>
            <label className="label-eyebrow">
              {type === "arxiv" ? "arXiv identifier" : "DOI"}
            </label>
            <input
              value={ref}
              onChange={(e) => setRef(e.target.value)}
              placeholder={type === "arxiv" ? "2401.12345" : "10.1145/…"}
              className="mt-2 h-9 w-full rounded-md border border-hairline-strong bg-background px-3 text-[13px] text-foreground focus:outline-none focus:ring-1 focus:ring-[color:var(--ring)]"
              autoFocus
            />
          </div>
          {error && (
            <div className="rounded-md border border-[color:var(--danger)]/30 bg-[color:var(--danger-soft)] px-3 py-2 text-[12px] text-[color:var(--danger)]">
              {error}
            </div>
          )}
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-hairline px-5 py-4">
          <button
            onClick={onClose}
            className="inline-flex h-8 items-center rounded-md px-3 text-[12px] text-muted-foreground hover:text-foreground"
          >
            Cancel
          </button>
          <button
            disabled={!ref || pending}
            onClick={() => onSubmit({ source_type: type, source_ref: ref })}
            className="inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-[12px] font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
          >
            {pending ? "Queuing…" : "Begin ingestion"} <ArrowRight className="size-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAtlassUser } from "@/lib/atlass-store";
import { AppShell } from "@/components/atlass/AppShell";
import { EmptyState } from "@/components/atlass/EmptyState";
import { ErrorState } from "@/components/atlass/ErrorState";
import { Skeleton } from "@/components/atlass/Skeleton";
import { Search } from "lucide-react";
import { clsx } from "clsx";

export const Route = createFileRoute("/app/knowledge")({
  component: KnowledgePage,
  head: () => ({ meta: [{ title: "Knowledge — ATLASS" }] }),
});

const KINDS = ["", "concept", "entity", "relation"];

function KnowledgePage() {
  const { user } = useAtlassUser();
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("");

  const items = useQuery({
    queryKey: ["knowledge-search", user?.id, q, kind],
    queryFn: () => api.knowledge.search(user!.id, q, kind || undefined, undefined, 100),
    enabled: !!user?.id,
    retry: false,
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-[1240px] px-6 py-10 sm:px-10">
        <div className="label-eyebrow">Cross-library index</div>
        <h1 className="mt-2 text-display text-4xl">Knowledge</h1>
        <p className="mt-3 max-w-xl text-[14px] text-muted-foreground">
          Search concepts, entities, and relations extracted from every paper in your library.
        </p>

        {/* Controls */}
        <div className="mt-8 flex flex-wrap items-center gap-2">
          <div className="flex h-10 min-w-[280px] flex-1 items-center gap-2 rounded-md border border-hairline bg-surface px-3">
            <Search className="size-4 text-muted-foreground" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search concepts, entities, relations…"
              className="w-full bg-transparent text-[13px] text-foreground placeholder:text-muted-foreground focus:outline-none"
            />
          </div>
          <div className="flex gap-1 rounded-md border border-hairline bg-surface p-0.5">
            {KINDS.map((k) => (
              <button
                key={k || "all"}
                onClick={() => setKind(k)}
                className={clsx(
                  "h-8 rounded-md px-3 text-[12px]",
                  kind === k
                    ? "bg-background text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {k || "All"}
              </button>
            ))}
          </div>
        </div>

        {/* Results table */}
        <div className="mt-6 overflow-hidden rounded-xl border border-hairline bg-surface">
          <div className="hidden grid-cols-[1.4fr_100px_1fr_80px_80px] gap-4 border-b border-hairline bg-surface-2/60 px-4 py-2 text-[10px] uppercase tracking-[0.14em] text-muted-foreground md:grid">
            <div>Label</div>
            <div>Kind</div>
            <div>Source sections</div>
            <div className="text-right">Freq</div>
            <div className="text-right">Score</div>
          </div>
          {items.isLoading ? (
            <div className="space-y-2 p-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-full" />
              ))}
            </div>
          ) : items.isError ? (
            <div className="p-4">
              <ErrorState
                title="Knowledge index unavailable"
                onRetry={() => items.refetch()}
              />
            </div>
          ) : !items.data || items.data.length === 0 ? (
            <EmptyState
              glyph="graph"
              title="No knowledge indexed yet."
              description="Once papers finish grounding, their extracted concepts, entities, and relations appear here."
            />
          ) : (
            <ul className="divide-y divide-hairline">
              {items.data.map((k, i) => (
                <li
                  key={i}
                  className="grid grid-cols-[1.4fr_100px_1fr_80px_80px] gap-4 px-4 py-2 text-[12.5px] transition hover:bg-surface-2/50"
                >
                  <div className="truncate text-foreground">{k.label}</div>
                  <div className="text-mono text-[11px] text-muted-foreground">{k.kind}</div>
                  <div className="truncate text-muted-foreground">
                    {k.sections?.join(" · ") ?? "—"}
                  </div>
                  <div className="text-right text-mono text-[11px] text-foreground/80">
                    {k.frequency ?? 1}
                  </div>
                  <div className="text-right text-mono text-[11px] text-[color:var(--evidence)]">
                    {k.score != null ? k.score.toFixed(2) : "—"}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </AppShell>
  );
}

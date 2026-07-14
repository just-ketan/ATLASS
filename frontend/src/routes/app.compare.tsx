import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, type CompareResult } from "@/lib/api";
import { useAtlassUser } from "@/lib/atlass-store";
import { AppShell } from "@/components/atlass/AppShell";
import { EmptyState } from "@/components/atlass/EmptyState";
import { ErrorState } from "@/components/atlass/ErrorState";
import { Skeleton, PipelineLoading } from "@/components/atlass/Skeleton";
import { StatusChip } from "@/components/atlass/StatusChip";
import { GitCompareArrows, Check } from "lucide-react";

export const Route = createFileRoute("/app/compare")({
  component: ComparePage,
  head: () => ({ meta: [{ title: "Compare — ATLASS" }] }),
});

const ASPECTS = ["method", "problem", "limitations", "results", "custom"] as const;
type Aspect = (typeof ASPECTS)[number];

function ComparePage() {
  const { user } = useAtlassUser();
  const userId = user?.id;
  const papers = useQuery({
    queryKey: ["papers", userId],
    queryFn: () => api.papers.list(userId!),
    enabled: !!userId,
    retry: false,
  });
  const [selected, setSelected] = useState<string[]>([]);
  const [aspect, setAspect] = useState<Aspect>("method");
  const [custom, setCustom] = useState("");

  const compare = useMutation({
    mutationFn: () =>
      api.papers.compare(userId!, {
        paper_ids: selected,
        aspect: aspect === "custom" ? custom : aspect,
      }),
  });

  const ready = useMemo(
    () => (papers.data ?? []).filter((p) => p.status === "ready" || p.is_demo),
    [papers.data],
  );

  return (
    <AppShell>
      <div className="mx-auto max-w-[1240px] px-6 py-10 sm:px-10">
        <div className="label-eyebrow">Multi-paper reasoning</div>
        <h1 className="mt-2 text-display text-4xl">Compare</h1>
        <p className="mt-3 max-w-xl text-[14px] text-muted-foreground">
          Select two or more grounded papers and choose a comparison aspect. ATLASS answers with
          side-by-side evidence and an extractive synthesis.
        </p>

        {/* Controls */}
        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="panel p-5">
            <div className="label-eyebrow">Select papers · minimum 2</div>
            {papers.isLoading ? (
              <div className="mt-4 space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : ready.length === 0 ? (
              <EmptyState
                glyph="compare"
                title="No ready papers to compare"
                description="Ingest and ground at least two papers to unlock multi-paper reasoning."
              />
            ) : (
              <ul className="mt-4 divide-y divide-hairline">
                {ready.map((p) => {
                  const isSel = selected.includes(p.id);
                  return (
                    <li key={p.id}>
                      <button
                        onClick={() =>
                          setSelected((s) =>
                            s.includes(p.id) ? s.filter((x) => x !== p.id) : [...s, p.id],
                          )
                        }
                        className="flex w-full items-center gap-3 py-3 text-left transition hover:bg-surface-2/50"
                      >
                        <span
                          className={
                            isSel
                              ? "flex size-4 items-center justify-center rounded border border-[color:var(--evidence)] bg-[color:var(--evidence-soft)] text-[color:var(--evidence)]"
                              : "size-4 rounded border border-hairline-strong"
                          }
                        >
                          {isSel && <Check className="size-3" strokeWidth={3} />}
                        </span>
                        <span className="min-w-0 flex-1 truncate text-[13px] text-foreground">
                          {p.title}
                        </span>
                        {p.is_demo && <StatusChip variant="warning">demo</StatusChip>}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <div className="panel p-5">
            <div className="label-eyebrow">Aspect</div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {ASPECTS.map((a) => (
                <button
                  key={a}
                  onClick={() => setAspect(a)}
                  className={
                    aspect === a
                      ? "rounded-md border border-[color:var(--evidence)]/40 bg-[color:var(--evidence-soft)] px-2.5 py-1 text-[12px] text-[color:var(--evidence)]"
                      : "rounded-md border border-hairline bg-surface px-2.5 py-1 text-[12px] text-muted-foreground hover:text-foreground"
                  }
                >
                  {a}
                </button>
              ))}
            </div>
            {aspect === "custom" && (
              <textarea
                value={custom}
                onChange={(e) => setCustom(e.target.value)}
                placeholder="Ask a custom comparison question…"
                rows={3}
                className="mt-3 w-full resize-none rounded-md border border-hairline-strong bg-background p-3 text-[13px] text-foreground focus:outline-none focus:ring-1 focus:ring-[color:var(--ring)]"
              />
            )}
            <button
              onClick={() => compare.mutate()}
              disabled={selected.length < 2 || compare.isPending || (aspect === "custom" && !custom)}
              className="mt-4 inline-flex h-10 w-full items-center justify-center gap-1.5 rounded-md bg-primary px-3 text-[13px] font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
            >
              <GitCompareArrows className="size-3.5" />
              {compare.isPending ? "Grounding comparison…" : `Compare ${selected.length || ""} papers`}
            </button>
            {compare.isPending && <div className="mt-3"><PipelineLoading label="Cross-retrieving · aligning claims · composing synthesis…" /></div>}
          </div>
        </div>

        {/* Results */}
        {compare.isError && (
          <ErrorState className="mt-8" title="Comparison failed" description={compare.error?.message} />
        )}
        {compare.data && <CompareResults result={compare.data} />}
      </div>
    </AppShell>
  );
}

function CompareResults({ result }: { result: CompareResult }) {
  return (
    <div className="mt-10 animate-fade-up">
      <div className="label-eyebrow">Result · aspect “{result.aspect}”</div>
      <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {result.papers.map((p, i) => (
          <div key={i} className="panel p-5">
            <div className="text-[11px] uppercase tracking-[0.14em] text-subtle">
              Paper · #{i + 1}
            </div>
            <div className="mt-1 text-[14px] font-medium text-foreground">
              {p.title ?? p.paper_id}
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">{p.summary}</p>
            {p.citations && p.citations.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {p.citations.slice(0, 4).map((c, j) => (
                  <span
                    key={j}
                    className="rounded-full border border-[color:var(--evidence)]/25 bg-[color:var(--evidence-soft)] px-2 py-0.5 text-mono text-[10px] text-[color:var(--evidence)]"
                  >
                    §{c.section ?? "?"}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      {result.synthesis && (
        <div className="mt-6 panel p-6">
          <div className="label-eyebrow">Extractive synthesis</div>
          <p className="mt-3 text-[14px] leading-relaxed text-foreground/90">{result.synthesis}</p>
        </div>
      )}
    </div>
  );
}

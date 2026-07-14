import { useEffect, useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api, STAGES } from "@/lib/api";
import { useAtlassUser } from "@/lib/atlass-store";
import { AppShell } from "@/components/atlass/AppShell";
import { WorkflowTimeline } from "@/components/atlass/WorkflowTimeline";
import { StatusChip, statusToVariant, humanStatus } from "@/components/atlass/StatusChip";
import { EmptyState } from "@/components/atlass/EmptyState";
import { ErrorState } from "@/components/atlass/ErrorState";
import { Skeleton } from "@/components/atlass/Skeleton";
import { ArrowRight, Plus, Sparkles, FileText, TrendingUp } from "lucide-react";

export const Route = createFileRoute("/app/")({
  component: OverviewPage,
  head: () => ({ meta: [{ title: "Overview — ATLASS" }] }),
});

function OverviewPage() {
  const { user, hydrated, signIn } = useAtlassUser();
  useEffect(() => {
    if (hydrated && !user) void signIn();
  }, [hydrated, user, signIn]);

  const userId = user?.id;
  const dashboard = useQuery({
    queryKey: ["dashboard", userId],
    queryFn: () => api.dashboard(userId!),
    enabled: !!userId,
    retry: false,
  });
  const papers = useQuery({
    queryKey: ["papers", userId],
    queryFn: () => api.papers.list(userId!),
    enabled: !!userId,
    retry: false,
  });

  const backendOffline = dashboard.isError && papers.isError;

  const recent = useMemo(() => {
    return dashboard.data?.recent_papers ?? papers.data ?? [];
  }, [dashboard.data, papers.data]);

  const counts = dashboard.data?.counts ?? {
    papers: papers.data?.length ?? 0,
    ready: papers.data?.filter((p) => p.status === "ready").length ?? 0,
    processing:
      papers.data?.filter((p) =>
        ["processing", "extracting_text", "creating_embeddings"].includes(p.status ?? ""),
      ).length ?? 0,
    projects: 0,
    knowledge: 0,
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-[1240px] px-6 py-10 sm:px-10 sm:py-14">
        {/* Editorial welcome */}
        <div className="animate-fade-up">
          <div className="label-eyebrow">
            {new Date().toLocaleDateString(undefined, {
              weekday: "long",
              month: "long",
              day: "numeric",
            })}
          </div>
          <h1 className="mt-3 text-display text-[44px] leading-[1.05] text-foreground sm:text-[56px]">
            Welcome back, {user?.name ?? "Researcher"}.
          </h1>
          <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
            Six papers await grounding. Continue where you left off, or ingest a new source to open
            the workflow.
          </p>
        </div>

        {backendOffline && (
          <ErrorState
            className="mt-8"
            title="ATLASS backend not reachable"
            description={
              <>
                The UI is running against{" "}
                <span className="text-mono text-foreground/90">{api.base}</span>. Start the backend
                to load your dashboard, or explore the interface with realistic empty states.
              </>
            }
            onRetry={() => {
              dashboard.refetch();
              papers.refetch();
            }}
          />
        )}

        {/* Metrics strip */}
        <div className="mt-10 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-hairline bg-hairline sm:grid-cols-4">
          {[
            { l: "Papers", v: counts.papers ?? 0, sub: "in library" },
            { l: "Ready", v: counts.ready ?? 0, sub: "fully grounded" },
            { l: "Processing", v: counts.processing ?? 0, sub: "in pipeline" },
            { l: "Knowledge", v: counts.knowledge ?? 0, sub: "concepts extracted" },
          ].map((m) => (
            <div key={m.l} className="bg-background p-5">
              <div className="label-eyebrow">{m.l}</div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-display text-[38px] leading-none text-foreground">
                  {dashboard.isLoading ? <Skeleton className="h-8 w-10" /> : m.v}
                </span>
                <span className="text-[12px] text-muted-foreground">{m.sub}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Workflow visual */}
        <section className="mt-14">
          <div className="mb-5 flex items-baseline justify-between">
            <div>
              <div className="label-eyebrow">The workflow</div>
              <h2 className="mt-1 text-display text-2xl">Paper to working system</h2>
            </div>
            <Link
              to="/app/library"
              className="text-[13px] text-muted-foreground hover:text-foreground"
            >
              Start a new paper →
            </Link>
          </div>
          <div className="panel p-6">
            <WorkflowTimeline current="spec" completed={["import", "understand"]} />
            <div className="mt-6 grid gap-3 text-[12px] text-muted-foreground sm:grid-cols-3">
              <div className="flex items-center gap-2">
                <span className="size-1.5 rounded-full bg-[color:var(--evidence)]" />
                Completed stages become calm
              </div>
              <div className="flex items-center gap-2">
                <span className="size-1.5 animate-pulse-soft rounded-full bg-[color:var(--evidence)]" />
                Current stage subtly glows
              </div>
              <div className="flex items-center gap-2">
                <span className="size-1.5 rounded-full bg-hairline-strong" />
                Future stages remain quiet
              </div>
            </div>
          </div>
        </section>

        {/* Two-column: continue + recent */}
        <section className="mt-14 grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          <div className="panel p-6">
            <div className="flex items-baseline justify-between">
              <div>
                <div className="label-eyebrow">Continue research</div>
                <h3 className="mt-1 text-display text-xl">Pick up where you left off</h3>
              </div>
              <Sparkles className="size-4 text-muted-foreground" />
            </div>
            <div className="mt-5 space-y-3">
              {dashboard.data?.continue?.length ? (
                dashboard.data.continue.map((c) => (
                  <Link
                    key={c.paper_id}
                    to="/app/paper/$paperId"
                    params={{ paperId: c.paper_id }}
                    className="group flex items-center gap-4 rounded-lg border border-hairline bg-background p-4 transition hover:bg-surface-2"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[14px] font-medium text-foreground">
                        {c.title}
                      </div>
                      <div className="mt-1 text-[11px] uppercase tracking-[0.14em] text-subtle">
                        Stage · {c.stage}
                      </div>
                    </div>
                    <ArrowRight className="size-4 text-muted-foreground transition group-hover:translate-x-0.5 group-hover:text-foreground" />
                  </Link>
                ))
              ) : (
                <EmptyState
                  glyph="spec"
                  title="No active session"
                  description="Open a paper to begin grounding evidence and building a specification."
                  action={
                    <Link
                      to="/app/library"
                      className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground hover:opacity-90"
                    >
                      Open library <ArrowRight className="size-3.5" />
                    </Link>
                  }
                />
              )}
            </div>
          </div>

          <div className="panel p-6">
            <div className="flex items-baseline justify-between">
              <div>
                <div className="label-eyebrow">Recent papers</div>
                <h3 className="mt-1 text-display text-xl">Last ingested</h3>
              </div>
              <TrendingUp className="size-4 text-muted-foreground" />
            </div>
            <div className="mt-5 divide-y divide-hairline">
              {papers.isLoading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3 py-3">
                    <Skeleton className="h-4 w-40" />
                    <Skeleton className="ml-auto h-4 w-16" />
                  </div>
                ))
              ) : recent.length ? (
                recent.slice(0, 5).map((p) => (
                  <Link
                    key={p.id}
                    to="/app/paper/$paperId"
                    params={{ paperId: p.id }}
                    className="flex items-center gap-3 py-3 text-[13px] transition hover:text-foreground"
                  >
                    <FileText className="size-3.5 shrink-0 text-muted-foreground" />
                    <span className="min-w-0 flex-1 truncate text-foreground/90">
                      {p.title}
                    </span>
                    <StatusChip variant={statusToVariant(p.status)}>
                      {humanStatus(p.status)}
                    </StatusChip>
                  </Link>
                ))
              ) : (
                <EmptyState
                  glyph="grid"
                  title="No papers in library"
                  description="Ingest a paper from arXiv or upload a PDF to begin."
                  action={
                    <Link
                      to="/app/library"
                      className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground hover:opacity-90"
                    >
                      <Plus className="size-3.5" /> Add first paper
                    </Link>
                  }
                />
              )}
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

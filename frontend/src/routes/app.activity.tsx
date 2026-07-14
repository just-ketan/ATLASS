import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAtlassUser } from "@/lib/atlass-store";
import { AppShell } from "@/components/atlass/AppShell";
import { EmptyState } from "@/components/atlass/EmptyState";
import { ErrorState } from "@/components/atlass/ErrorState";
import { Skeleton } from "@/components/atlass/Skeleton";
import { StatusChip, humanStatus, statusToVariant } from "@/components/atlass/StatusChip";

export const Route = createFileRoute("/app/activity")({
  component: ActivityPage,
  head: () => ({ meta: [{ title: "Activity — ATLASS" }] }),
});

function ActivityPage() {
  const { user } = useAtlassUser();
  const papers = useQuery({
    queryKey: ["papers", user?.id],
    queryFn: () => api.papers.list(user!.id),
    enabled: !!user?.id,
    retry: false,
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-[900px] px-6 py-10 sm:px-10">
        <div className="label-eyebrow">Activity</div>
        <h1 className="mt-2 text-display text-4xl">Processing timeline</h1>
        <p className="mt-3 text-[14px] text-muted-foreground">
          A durable trace of every pipeline stage across your library — visible, auditable,
          reversible.
        </p>

        <div className="mt-8">
          {papers.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : papers.isError ? (
            <ErrorState onRetry={() => papers.refetch()} />
          ) : !papers.data || papers.data.length === 0 ? (
            <EmptyState
              glyph="grid"
              title="No activity to display."
              description="Once you ingest a paper, its pipeline events will stream here."
            />
          ) : (
            <ol className="relative space-y-4 border-l border-hairline pl-6">
              {papers.data.map((p) => (
                <li key={p.id} className="relative">
                  <span className="absolute -left-[29px] top-1.5 size-2.5 rounded-full bg-[color:var(--evidence)] ring-4 ring-[color:var(--evidence-soft)]" />
                  <div className="flex flex-wrap items-baseline gap-3">
                    <div className="text-[14px] font-medium text-foreground">{p.title}</div>
                    <StatusChip variant={statusToVariant(p.status)}>
                      {humanStatus(p.status)}
                    </StatusChip>
                    <span className="text-mono text-[11px] text-muted-foreground">
                      {p.created_at ? new Date(p.created_at).toLocaleString() : ""}
                    </span>
                  </div>
                  <div className="mt-1 text-[12px] text-muted-foreground">
                    {p.source_type?.toUpperCase()} · {p.source_ref ?? p.id}
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </AppShell>
  );
}

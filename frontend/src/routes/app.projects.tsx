import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAtlassUser } from "@/lib/atlass-store";
import { AppShell } from "@/components/atlass/AppShell";
import { EmptyState } from "@/components/atlass/EmptyState";
import { Plus, FolderKanban } from "lucide-react";

export const Route = createFileRoute("/app/projects")({
  component: ProjectsPage,
  head: () => ({ meta: [{ title: "Projects — ATLASS" }] }),
});

function ProjectsPage() {
  const { user } = useAtlassUser();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const projects = useQuery({
    queryKey: ["projects", user?.id],
    queryFn: () => api.projects.list(user!.id),
    enabled: !!user?.id,
    retry: false,
  });

  const create = useMutation({
    mutationFn: (n: string) => api.projects.create(user!.id, { name: n }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects", user?.id] });
      setName("");
      setCreating(false);
    },
    onError: () => {
      // Show error inline; no fake persistence.
      setCreating(false);
    },
  });

  return (
    <AppShell>
      <div className="mx-auto max-w-[1240px] px-6 py-10 sm:px-10">
        <div className="flex items-end justify-between">
          <div>
            <div className="label-eyebrow">Research memory</div>
            <h1 className="mt-2 text-display text-4xl">Projects</h1>
            <p className="mt-3 max-w-xl text-[14px] text-muted-foreground">
              Group related papers, datasets, and notes into a persistent research context.
            </p>
          </div>
          <button
            onClick={() => setCreating(true)}
            className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-3 text-[13px] font-medium text-primary-foreground hover:opacity-90"
          >
            <Plus className="size-3.5" /> New project
          </button>
        </div>

        {creating && (
          <div className="mt-6 panel p-5">
            <div className="label-eyebrow">Create project</div>
            <div className="mt-3 flex gap-2">
              <input
                autoFocus
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Long-context attention survey"
                className="h-9 flex-1 rounded-md border border-hairline-strong bg-background px-3 text-[13px] text-foreground focus:outline-none focus:ring-1 focus:ring-[color:var(--ring)]"
              />
              <button
                disabled={!name || create.isPending}
                onClick={() => create.mutate(name)}
                className="inline-flex h-9 items-center rounded-md bg-primary px-3 text-[13px] font-medium text-primary-foreground disabled:opacity-60"
              >
                {create.isPending ? "Creating…" : "Create"}
              </button>
              <button
                onClick={() => setCreating(false)}
                className="inline-flex h-9 items-center rounded-md px-3 text-[13px] text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
            </div>
            {create.isError && (
              <div className="mt-2 text-[12px] text-[color:var(--danger)]">
                {create.error?.message}
              </div>
            )}
          </div>
        )}

        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {projects.isLoading ? (
            <div className="col-span-full panel p-5 text-[13px] text-muted-foreground">Loading projects…</div>
          ) : projects.isError ? (
            <div className="col-span-full panel p-5 text-[13px] text-[color:var(--danger)]">{projects.error.message}</div>
          ) : !projects.data?.length ? (
            <div className="col-span-full">
              <EmptyState
                glyph="grid"
                title="No projects yet"
                description="Projects are lightweight containers for a stream of research: papers, datasets, notes, and conversations."
              />
            </div>
          ) : (
            projects.data.map((p: any) => (
              <div key={p.id} className="panel p-5">
                <FolderKanban className="size-4 text-muted-foreground" />
                <div className="mt-3 text-[15px] font-medium text-foreground">{p.name}</div>
                <div className="mt-1 text-[11px] uppercase tracking-[0.14em] text-subtle">
                  Created {new Date(p.created_at).toLocaleDateString()}
                </div>
                <div className="mt-4 flex gap-4 text-[11px] text-muted-foreground">
                  <span>0 papers</span>
                  <span>0 notes</span>
                  <span>0 datasets</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}

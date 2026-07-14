import { useEffect, useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  api,
  STAGES,
  type StageId,
  type SystemSpec,
  type Blueprint,
  type BaselineProject,
  type RunReport,
  type AskAnswer,
  type EventRecord,
  type KnowledgeItem,
} from "@/lib/api";
import { useAtlassUser } from "@/lib/atlass-store";
import { AppShell } from "@/components/atlass/AppShell";
import { WorkflowTimeline } from "@/components/atlass/WorkflowTimeline";
import { StatusChip, statusToVariant, humanStatus } from "@/components/atlass/StatusChip";
import { EmptyState } from "@/components/atlass/EmptyState";
import { ErrorState } from "@/components/atlass/ErrorState";
import { Skeleton, SkeletonBlock, PipelineLoading } from "@/components/atlass/Skeleton";
import { EvidencePanel, ConfidenceBar } from "@/components/atlass/EvidencePanel";
import { JsonInspector } from "@/components/atlass/JsonInspector";
import {
  ArrowLeft,
  Send,
  CheckCircle2,
  FileText,
  Folder,
  Play,
  Terminal,
  BookOpen,
} from "lucide-react";
import { clsx } from "clsx";

export const Route = createFileRoute("/app/paper/$paperId")({
  component: PaperWorkspace,
  head: () => ({ meta: [{ title: "Workspace — ATLASS" }] }),
});

const SPEC_FIELD_ORDER = [
  "problem_statement",
  "contribution",
  "task_definition",
  "inputs",
  "outputs",
  "model_components",
  "objective",
  "training_setup",
  "datasets",
  "preprocessing",
  "metrics",
  "baselines",
  "reported_results",
  "limitations",
];

function PaperWorkspace() {
  const { paperId } = Route.useParams();
  const { user, signIn } = useAtlassUser();
  useEffect(() => {
    if (!user) void signIn();
  }, [user, signIn]);
  const userId = user?.id;
  const [stage, setStage] = useState<StageId>("understand");
  const [activeEvidence, setActiveEvidence] = useState<{
    title: string;
    citations?: any[];
    confidence?: number;
    sections?: string[];
    assumptions?: string[];
  } | null>(null);

  const papers = useQuery({
    queryKey: ["papers", userId],
    queryFn: () => api.papers.list(userId!),
    enabled: !!userId,
    retry: false,
  });
  const paper = papers.data?.find((p) => p.id === paperId);

  const events = useQuery({
    queryKey: ["events", userId, paperId],
    queryFn: () => api.papers.events(userId!, paperId),
    enabled: !!userId,
    retry: false,
    refetchInterval: 6000,
  });

  const spec = useQuery({
    queryKey: ["spec", userId, paperId],
    queryFn: () => api.spec.get(userId!, paperId),
    enabled: !!userId && stage === "spec",
    retry: false,
  });
  const blueprint = useQuery({
    queryKey: ["blueprint", userId, paperId],
    queryFn: () => api.blueprint.get(userId!, paperId),
    enabled: !!userId && stage === "blueprint",
    retry: false,
  });
  const baseline = useQuery({
    queryKey: ["baseline", userId, paperId],
    queryFn: () => api.baseline.get(userId!, paperId),
    enabled: !!userId && stage === "baseline",
    retry: false,
  });
  const report = useQuery({
    queryKey: ["report", userId, paperId],
    queryFn: () => api.baseline.report(userId!, paperId),
    enabled: !!userId && stage === "report",
    retry: false,
  });
  const knowledge = useQuery({
    queryKey: ["knowledge", userId, paperId],
    queryFn: () => api.papers.knowledge(userId!, paperId),
    enabled: !!userId && stage === "understand",
    retry: false,
  });

  const completed = useMemo<StageId[]>(() => {
    const done: StageId[] = [];
    if (paper?.status === "ready") done.push("import", "understand");
    if (spec.data?.approved) done.push("spec");
    if (blueprint.data?.approved) done.push("blueprint");
    if (baseline.data) done.push("baseline");
    if (report.data?.status === "succeeded") done.push("report");
    return Array.from(new Set(done));
  }, [paper, spec.data, blueprint.data, baseline.data, report.data]);

  const backendOffline = papers.isError;

  return (
    <AppShell contextPaper={paper ? { id: paper.id, title: paper.title } : null} right={
      <EvidenceDrawer active={activeEvidence} />
    }>
      <div className="flex min-h-[calc(100dvh-56px)] flex-col">
        {/* Workspace header */}
        <div className="hairline-b bg-background px-6 py-6 sm:px-10">
          <Link
            to="/app/library"
            className="inline-flex items-center gap-1.5 text-[12px] text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-3.5" /> Library
          </Link>
          <div className="mt-4 flex flex-wrap items-start justify-between gap-6">
            <div className="min-w-0">
              <div className="label-eyebrow">
                {paper?.source_type?.toUpperCase() ?? "PAPER"} ·{" "}
                {paper?.source_ref ?? paperId}
              </div>
              <h1 className="mt-2 text-display text-[32px] leading-tight text-foreground sm:text-[38px]">
                {paper?.title ?? (papers.isLoading ? <Skeleton className="h-8 w-96" /> : "Untitled paper")}
              </h1>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[12px] text-muted-foreground">
                {paper?.status && (
                  <StatusChip variant={statusToVariant(paper.status)}>
                    {humanStatus(paper.status)}
                  </StatusChip>
                )}
                {paper?.is_demo && (
                  <StatusChip variant="warning">Synthetic fixture · not a real paper</StatusChip>
                )}
                {paper?.authors && <span>{paper.authors.slice(0, 3).join(" · ")}</span>}
              </div>
            </div>
          </div>

          <div className="mt-8">
            <WorkflowTimeline current={stage} completed={completed} onSelect={setStage} />
          </div>
        </div>

        {backendOffline && (
          <div className="p-6 sm:p-10">
            <ErrorState
              title="Backend not reachable"
              description={
                <>
                  This workspace needs a running ATLASS backend at{" "}
                  <span className="text-mono">{api.base}</span>. The UI below shows realistic empty
                  states.
                </>
              }
              onRetry={() => papers.refetch()}
            />
          </div>
        )}

        {/* Stage body */}
        <div className="flex-1 px-6 py-8 sm:px-10">
          {stage === "import" && <ImportStage events={events.data} loading={events.isLoading} />}
          {stage === "understand" && (
            <UnderstandStage
              userId={userId}
              paperId={paperId}
              knowledge={knowledge.data}
              knowledgeLoading={knowledge.isLoading}
              onEvidence={setActiveEvidence}
            />
          )}
          {stage === "spec" && (
            <SpecStage
              userId={userId}
              paperId={paperId}
              spec={spec.data}
              loading={spec.isLoading}
              onEvidence={setActiveEvidence}
            />
          )}
          {stage === "blueprint" && (
            <BlueprintStage
              userId={userId}
              paperId={paperId}
              blueprint={blueprint.data}
              loading={blueprint.isLoading}
              onEvidence={setActiveEvidence}
            />
          )}
          {stage === "baseline" && (
            <BaselineStage
              userId={userId}
              paperId={paperId}
              baseline={baseline.data}
              loading={baseline.isLoading}
            />
          )}
          {stage === "report" && (
            <ReportStage
              userId={userId}
              paperId={paperId}
              report={report.data}
              loading={report.isLoading}
            />
          )}
        </div>
      </div>
    </AppShell>
  );
}

function EvidenceDrawer({ active }: { active: any }) {
  return (
    <div className="px-5 py-6">
      <div className="mb-4 flex items-center justify-between">
        <div className="label-eyebrow">Provenance</div>
        <span className="text-[10px] text-subtle">Sticky · resizes with viewport</span>
      </div>
      {active ? (
        <>
          <div className="text-[13px] font-medium text-foreground">{active.title}</div>
          <div className="mt-4">
            <EvidencePanel
              citations={active.citations}
              confidence={active.confidence}
              sections={active.sections}
              assumptions={active.assumptions}
            />
          </div>
        </>
      ) : (
        <div className="rounded-lg border border-hairline border-dashed bg-surface/60 p-5 text-center text-[12px] text-muted-foreground">
          Hover an answer, spec field, or module to reveal its retrieved sections, citations,
          confidence, and assumptions.
        </div>
      )}
    </div>
  );
}

// ---------------- Import ----------------
function ImportStage({ events, loading }: { events?: EventRecord[]; loading: boolean }) {
  return (
    <div className="mx-auto max-w-3xl">
      <div className="label-eyebrow">Stage 01 · Import</div>
      <h2 className="mt-2 text-display text-3xl">Ingestion timeline</h2>
      <p className="mt-3 text-[14px] text-muted-foreground">
        The paper is fetched, parsed, chunked, and embedded. Each step emits a durable event so
        you can audit exactly what ATLASS saw.
      </p>
      <div className="mt-8 panel p-6">
        {loading ? (
          <SkeletonBlock rows={5} />
        ) : !events || events.length === 0 ? (
          <EmptyState
            glyph="flask"
            title="No pipeline events yet"
            description="Events will stream in as the ingestion pipeline runs."
          />
        ) : (
          <ol className="relative space-y-4 border-l border-hairline pl-5">
            {events.map((e, i) => (
              <li key={i} className="relative">
                <span
                  className={clsx(
                    "absolute -left-[26px] top-1.5 size-2.5 rounded-full ring-4",
                    e.status === "failed"
                      ? "bg-[color:var(--danger)] ring-[color:var(--danger-soft)]"
                      : e.status === "done"
                        ? "bg-[color:var(--evidence)] ring-[color:var(--evidence-soft)]"
                        : e.status === "running"
                          ? "animate-pulse-soft bg-[color:var(--info)] ring-[color:var(--info)]/20"
                          : "bg-hairline-strong ring-hairline",
                  )}
                />
                <div className="flex items-center justify-between text-[13px]">
                  <span className="text-foreground">{humanStatus(e.stage)}</span>
                  <span className="text-mono text-[11px] text-muted-foreground">
                    {e.at ?? e.ts ?? ""}
                  </span>
                </div>
                {e.message && (
                  <div className="mt-1 text-[12px] text-muted-foreground">{e.message}</div>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

// ---------------- Understand ----------------
function UnderstandStage({
  userId,
  paperId,
  knowledge,
  knowledgeLoading,
  onEvidence,
}: {
  userId?: string;
  paperId: string;
  knowledge?: KnowledgeItem[];
  knowledgeLoading: boolean;
  onEvidence: (v: any) => void;
}) {
  const [question, setQuestion] = useState("");
  const [answers, setAnswers] = useState<{ q: string; a: AskAnswer }[]>([]);
  const ask = useMutation({
    mutationFn: async (q: string) => api.papers.ask(userId!, paperId, q, false),
    onSuccess: (a, q) => {
      setAnswers((prev) => [{ q, a }, ...prev]);
      setQuestion("");
      onEvidence({
        title: q,
        citations: a.citations,
        confidence: a.confidence,
        sections: a.sections,
        assumptions: a.assumptions,
      });
    },
  });

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
      <div className="min-w-0">
        <div className="label-eyebrow">Stage 02 · Understand</div>
        <h2 className="mt-2 text-display text-3xl">Grounded evidence notebook</h2>
        <p className="mt-3 max-w-2xl text-[14px] text-muted-foreground">
          Ask about method, contributions, training setup, or results. Every answer is anchored to
          retrieved sections with an explicit confidence score.
        </p>

        {/* Composer */}
        <div className="mt-8 panel overflow-hidden">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What is the training objective? Which dataset was used? What ablations did the authors report?"
            rows={3}
            className="w-full resize-none bg-transparent px-5 py-4 text-[14px] leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none"
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && question) {
                ask.mutate(question);
              }
            }}
          />
          <div className="flex items-center justify-between border-t border-hairline bg-surface-2/40 px-4 py-2.5">
            <span className="text-[11px] text-subtle">
              <span className="text-mono">⌘↩</span> to ask · grounded in retrieved sections only
            </span>
            <button
              disabled={!question || ask.isPending}
              onClick={() => ask.mutate(question)}
              className="inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-[12px] font-medium text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
            >
              {ask.isPending ? "Grounding…" : "Ask"} <Send className="size-3.5" />
            </button>
          </div>
        </div>

        {ask.isError && (
          <ErrorState className="mt-4" title="Could not ground the question" description={ask.error?.message} />
        )}

        {/* Answers */}
        <div className="mt-8 space-y-4">
          {answers.length === 0 && !ask.isPending && (
            <EmptyState
              glyph="spec"
              title="No evidence has been grounded yet."
              description="Ask your first question above. ATLASS will retrieve the relevant sections and answer only from what it can cite."
            />
          )}
          {ask.isPending && (
            <div className="panel p-5">
              <PipelineLoading label="Retrieving sections · scoring evidence · composing answer…" />
              <div className="mt-4 space-y-2">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-11/12" />
                <Skeleton className="h-3 w-8/12" />
              </div>
            </div>
          )}
          {answers.map((a, i) => (
            <article
              key={i}
              className="panel p-5 animate-fade-up"
              onMouseEnter={() =>
                onEvidence({
                  title: a.q,
                  citations: a.a.citations,
                  confidence: a.a.confidence,
                  sections: a.a.sections,
                  assumptions: a.a.assumptions,
                })
              }
            >
              <div className="text-[11px] uppercase tracking-[0.14em] text-subtle">
                Question · #{answers.length - i}
              </div>
              <div className="mt-1 text-[14px] font-medium text-foreground/90">{a.q}</div>
              <div className="mt-4 border-l-2 border-[color:var(--evidence)]/40 pl-4 text-[14px] leading-relaxed text-foreground">
                {a.a.answer}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                {a.a.confidence != null && (
                  <StatusChip variant="confidence">
                    Confidence {(a.a.confidence * 100).toFixed(0)}%
                  </StatusChip>
                )}
                {a.a.citations?.slice(0, 4).map((c, j) => (
                  <span
                    key={j}
                    className="rounded-full border border-[color:var(--evidence)]/25 bg-[color:var(--evidence-soft)] px-2 py-0.5 text-[11px] text-mono text-[color:var(--evidence)]"
                  >
                    §{c.section ?? "?"}
                  </span>
                ))}
                {a.a.assumptions?.length ? (
                  <StatusChip variant="warning">{a.a.assumptions.length} assumption(s)</StatusChip>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </div>

      {/* Knowledge sidebar */}
      <div className="min-w-0">
        <div className="label-eyebrow">Knowledge</div>
        <div className="mt-3 panel p-4">
          {knowledgeLoading ? (
            <SkeletonBlock rows={5} />
          ) : !knowledge || knowledge.length === 0 ? (
            <div className="text-[12px] text-muted-foreground">
              Concepts and entities will appear here once the paper is grounded.
            </div>
          ) : (
            <ul className="space-y-1.5">
              {knowledge.slice(0, 14).map((k, i) => (
                <li key={i} className="flex items-center gap-2 text-[12px]">
                  <span
                    className={clsx(
                      "size-1 rounded-full",
                      k.kind === "concept" && "bg-[color:var(--evidence)]",
                      k.kind === "entity" && "bg-[color:var(--info)]",
                      k.kind === "relation" && "bg-[color:var(--warning)]",
                    )}
                  />
                  <span className="min-w-0 flex-1 truncate text-foreground/90">{k.label}</span>
                  <span className="text-mono text-[10px] text-muted-foreground">
                    {k.frequency ?? 1}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------- Spec ----------------
function SpecStage({
  userId,
  paperId,
  spec,
  loading,
  onEvidence,
}: {
  userId?: string;
  paperId: string;
  spec?: SystemSpec;
  loading: boolean;
  onEvidence: (v: any) => void;
}) {
  const qc = useQueryClient();
  const generate = useMutation({
    mutationFn: () => api.spec.generate(userId!, paperId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["spec", userId, paperId] }),
  });
  const approve = useMutation({
    mutationFn: () => api.spec.patch(userId!, paperId, { approve: true }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["spec", userId, paperId] }),
  });

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <SkeletonBlock rows={2} />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!spec) {
    return (
      <div className="mx-auto max-w-2xl">
        <EmptyState
          glyph="spec"
          eyebrow="Stage 03 · System Specification"
          title="No specification has been generated."
          description="Generate a structured design document from the grounded evidence. Every field will carry its source citations."
          action={
            <button
              onClick={() => generate.mutate()}
              disabled={generate.isPending}
              className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
            >
              {generate.isPending ? "Generating specification…" : "Generate specification"}
            </button>
          }
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <div className="flex items-start justify-between gap-6">
        <div>
          <div className="label-eyebrow">Stage 03 · System Specification</div>
          <h2 className="mt-2 text-display text-3xl">Proposed system, structured</h2>
          <p className="mt-3 max-w-xl text-[14px] text-muted-foreground">
            A design document — not raw JSON. Every field labels its provenance: supported,
            user-edited, assumption, or missing.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {spec.approved ? (
            <StatusChip variant="evidence">
              <CheckCircle2 className="size-3" /> Approved · v{spec.version ?? 1}
            </StatusChip>
          ) : (
            <button
              onClick={() => approve.mutate()}
              disabled={approve.isPending}
              className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-3 text-[13px] font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
            >
              <CheckCircle2 className="size-3.5" /> Approve
            </button>
          )}
        </div>
      </div>

      <div className="mt-8 space-y-3">
        {SPEC_FIELD_ORDER.map((k) => {
          const f = spec.fields?.[k];
          if (!f) return null;
          const status =
            f.status ?? (f.assumption ? "assumption" : f.value ? "supported" : "missing");
          return (
            <div
              key={k}
              className="group panel p-5 transition hover:border-hairline-strong"
              onMouseEnter={() =>
                onEvidence({
                  title: humanStatus(k),
                  citations: f.citations,
                  confidence: f.confidence,
                  assumptions: f.assumption ? ["Field is an ATLASS assumption"] : [],
                })
              }
            >
              <div className="flex items-baseline justify-between gap-3">
                <div>
                  <div className="label-eyebrow">{humanStatus(k)}</div>
                </div>
                <StatusChip variant={statusToVariant(status)}>{humanStatus(status)}</StatusChip>
              </div>
              <div className="mt-3 text-[15px] leading-relaxed text-foreground">
                {renderSpecValue(f.value) || (
                  <span className="text-muted-foreground italic">
                    No supporting evidence in the paper.
                  </span>
                )}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px]">
                {f.confidence != null && (
                  <span className="text-mono text-muted-foreground">
                    confidence {(f.confidence * 100).toFixed(0)}%
                  </span>
                )}
                {f.citations?.slice(0, 3).map((c, i) => (
                  <span
                    key={i}
                    className="rounded-full border border-[color:var(--evidence)]/25 bg-[color:var(--evidence-soft)] px-2 py-0.5 text-mono text-[color:var(--evidence)]"
                  >
                    §{c.section ?? "?"}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8">
        <JsonInspector data={spec} label="Raw specification JSON" />
      </div>
    </div>
  );
}

function renderSpecValue(v: unknown): string {
  if (v == null) return "";
  if (typeof v === "string") return v;
  if (Array.isArray(v)) return v.join(", ");
  return JSON.stringify(v);
}

// ---------------- Blueprint ----------------
function BlueprintStage({
  userId,
  paperId,
  blueprint,
  loading,
  onEvidence,
}: {
  userId?: string;
  paperId: string;
  blueprint?: Blueprint;
  loading: boolean;
  onEvidence: (v: any) => void;
}) {
  const qc = useQueryClient();
  const generate = useMutation({
    mutationFn: () => api.blueprint.generate(userId!, paperId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blueprint", userId, paperId] }),
  });
  const approve = useMutation({
    mutationFn: () => api.blueprint.patch(userId!, paperId, { approve: true }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["blueprint", userId, paperId] }),
  });

  if (loading) return <SkeletonBlock rows={6} />;
  if (!blueprint) {
    return (
      <EmptyState
        glyph="graph"
        eyebrow="Stage 04 · Implementation Blueprint"
        title="No blueprint has been generated."
        description="Turn the approved specification into a module-level implementation plan, with traceability back to source sections."
        action={
          <button
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
          >
            {generate.isPending ? "Composing blueprint…" : "Generate blueprint"}
          </button>
        }
      />
    );
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_1fr]">
      <div>
        <div className="label-eyebrow">Stage 04 · Implementation Blueprint</div>
        <h2 className="mt-2 text-display text-3xl">Architecture review</h2>
        <div className="mt-6 panel p-5">
          <div className="label-eyebrow mb-3">Project tree · module responsibilities</div>
          <ul className="space-y-1">
            {blueprint.modules?.map((m, i) => (
              <li
                key={i}
                onMouseEnter={() =>
                  onEvidence({
                    title: m.path,
                    citations: m.citations,
                    assumptions: m.assumption ? ["ATLASS baseline assumption"] : [],
                  })
                }
                className="group flex items-start gap-3 rounded-md px-2 py-2 transition hover:bg-surface-2"
              >
                <Folder className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <div className="text-mono text-[12px] text-foreground">{m.path}</div>
                  <div className="mt-0.5 text-[12px] leading-relaxed text-muted-foreground">
                    {m.responsibility}
                  </div>
                </div>
                {m.assumption && <StatusChip variant="warning">assumption</StatusChip>}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div>
        <div className="mt-8 lg:mt-0 flex items-center justify-between">
          <div className="label-eyebrow">Training plan · dependencies · config</div>
          {blueprint.approved ? (
            <StatusChip variant="evidence">Approved</StatusChip>
          ) : (
            <button
              onClick={() => approve.mutate()}
              className="inline-flex h-8 items-center gap-1.5 rounded-md bg-primary px-3 text-[12px] font-medium text-primary-foreground hover:opacity-90"
            >
              <CheckCircle2 className="size-3.5" /> Approve blueprint
            </button>
          )}
        </div>

        {blueprint.training_plan && (
          <div className="mt-3 panel p-5 text-[13px] leading-relaxed text-foreground/90">
            {blueprint.training_plan}
          </div>
        )}

        {blueprint.dependencies && blueprint.dependencies.length > 0 && (
          <div className="mt-3 panel p-5">
            <div className="label-eyebrow mb-3">Dependencies</div>
            <div className="flex flex-wrap gap-1.5">
              {blueprint.dependencies.map((d) => (
                <span
                  key={d}
                  className="rounded-md border border-hairline bg-surface px-2 py-1 text-mono text-[11px] text-foreground/85"
                >
                  {d}
                </span>
              ))}
            </div>
          </div>
        )}

        {blueprint.assumptions && blueprint.assumptions.length > 0 && (
          <div className="mt-3 panel border-[color:var(--warning)]/30 bg-[color:var(--warning-soft)]/40 p-5">
            <div className="label-eyebrow mb-2 text-[color:var(--warning)]">Open assumptions</div>
            <ul className="list-disc space-y-1 pl-4 text-[13px] text-foreground/90">
              {blueprint.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-6">
          <JsonInspector data={blueprint} label="Raw blueprint JSON" />
        </div>
      </div>
    </div>
  );
}

// ---------------- Baseline ----------------
function BaselineStage({
  userId,
  paperId,
  baseline,
  loading,
}: {
  userId?: string;
  paperId: string;
  baseline?: BaselineProject;
  loading: boolean;
}) {
  const qc = useQueryClient();
  const generate = useMutation({
    mutationFn: () => api.baseline.generate(userId!, paperId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["baseline", userId, paperId] }),
  });
  const run = useMutation({
    mutationFn: () => api.baseline.run(userId!, paperId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["report", userId, paperId] }),
  });

  if (loading) return <SkeletonBlock rows={6} />;
  if (!baseline) {
    return (
      <EmptyState
        glyph="flask"
        eyebrow="Stage 05 · Runnable Baseline"
        title="No baseline project has been generated."
        description="ATLASS produces a constrained PyTorch scaffold from the approved blueprint. This is a baseline — not a guaranteed reproduction of paper metrics."
        action={
          <button
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
          >
            {generate.isPending ? "Scaffolding baseline…" : "Generate baseline"}
          </button>
        }
      />
    );
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_1fr]">
      <div>
        <div className="label-eyebrow">Stage 05 · Runnable Baseline</div>
        <h2 className="mt-2 text-display text-3xl">Generated project</h2>

        <div className="mt-6 panel overflow-hidden">
          <div className="flex items-center gap-2 border-b border-hairline bg-surface-2/60 px-4 py-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
            <Folder className="size-3.5" /> Project tree
          </div>
          <ul className="max-h-[420px] overflow-y-auto p-3 text-mono text-[12px] leading-6">
            {(baseline.file_tree ?? []).map((f) => (
              <li key={f} className="flex items-center gap-2 text-foreground/85">
                <FileText className="size-3 text-muted-foreground" />
                <span>{f}</span>
              </li>
            ))}
            {(!baseline.file_tree || baseline.file_tree.length === 0) && (
              <li className="text-muted-foreground">No files listed.</li>
            )}
          </ul>
        </div>

        {baseline.run_command && (
          <div className="mt-4 panel">
            <div className="flex items-center gap-2 border-b border-hairline bg-surface-2/60 px-4 py-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              <Terminal className="size-3.5" /> Run command
            </div>
            <pre className="overflow-x-auto p-4 text-mono text-[12px] text-[color:var(--evidence)]">
              $ {baseline.run_command}
            </pre>
          </div>
        )}
      </div>

      <div>
        <div className="panel border-[color:var(--warning)]/30 bg-[color:var(--warning-soft)]/40 p-5">
          <div className="label-eyebrow text-[color:var(--warning)]">Scope warning</div>
          <p className="mt-2 text-[13px] leading-relaxed text-foreground/90">
            This is a <b>baseline approximation</b> derived from evidence-backed decisions plus
            explicit assumptions. It is not a guaranteed reproduction of the original paper's
            reported results. Human review is recommended before drawing scientific conclusions.
          </p>
        </div>

        {baseline.supported_families && (
          <div className="mt-4 panel p-5">
            <div className="label-eyebrow mb-3">Supported model families</div>
            <div className="flex flex-wrap gap-1.5">
              {baseline.supported_families.map((f) => (
                <span
                  key={f}
                  className="rounded-full border border-[color:var(--evidence)]/25 bg-[color:var(--evidence-soft)] px-2 py-0.5 text-mono text-[11px] text-[color:var(--evidence)]"
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        )}

        {baseline.warnings && baseline.warnings.length > 0 && (
          <div className="mt-4 panel p-5">
            <div className="label-eyebrow mb-2">Unsupported paper details</div>
            <ul className="list-disc space-y-1 pl-4 text-[13px] text-muted-foreground">
              {baseline.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-6 flex flex-wrap gap-2">
          <button
            onClick={() => run.mutate()}
            disabled={run.isPending}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground hover:opacity-90 disabled:opacity-60"
          >
            <Play className="size-3.5" /> {run.isPending ? "Launching smoke run…" : "Run smoke experiment"}
          </button>
          <button
            onClick={() => generate.mutate()}
            className="inline-flex h-10 items-center gap-2 rounded-md border border-hairline-strong bg-surface px-4 text-[13px] font-medium text-foreground hover:bg-surface-2"
          >
            Regenerate baseline
          </button>
        </div>

        <div className="mt-6">
          <JsonInspector data={baseline.manifest ?? baseline} label="Project manifest" />
        </div>
      </div>
    </div>
  );
}

// ---------------- Report ----------------
function ReportStage({
  userId,
  paperId,
  report,
  loading,
}: {
  userId?: string;
  paperId: string;
  report?: RunReport;
  loading: boolean;
}) {
  const [tab, setTab] = useState<"metrics" | "stdout" | "stderr">("metrics");

  if (loading) return <SkeletonBlock rows={6} />;
  if (!report) {
    return (
      <EmptyState
        glyph="flask"
        eyebrow="Stage 06 · Reproduction Report"
        title="No run has been completed."
        description="After a baseline smoke run, ATLASS will render observed metrics against paper-reported metrics with a comparability verdict."
      />
    );
  }

  const notComparable = report.comparability === "not_comparable";

  return (
    <div className="mx-auto max-w-4xl">
      <div className="label-eyebrow">Stage 06 · Reproduction Report</div>
      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-4">
        <h2 className="text-display text-3xl">Experiment notebook</h2>
        <StatusChip variant={statusToVariant(report.status)}>{humanStatus(report.status)}</StatusChip>
      </div>

      {notComparable && (
        <div className="mt-6 panel border-[color:var(--warning)]/30 bg-[color:var(--warning-soft)]/40 p-6">
          <div className="label-eyebrow text-[color:var(--warning)]">
            Comparability · not comparable to paper metrics
          </div>
          <p className="mt-2 text-[14px] leading-relaxed text-foreground/90">
            {report.verdict ??
              "This synthetic smoke run cannot be fairly compared to the paper's reported results due to reduced compute, dataset scale, or missing hyperparameters. Treat observed metrics as a sanity signal only."}
          </p>
        </div>
      )}

      {/* Metrics table */}
      <div className="mt-6 panel overflow-hidden">
        <div className="flex items-center gap-1 border-b border-hairline bg-surface-2/60 px-2 py-1.5">
          {(["metrics", "stdout", "stderr"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={clsx(
                "rounded-md px-3 py-1 text-[12px]",
                tab === t
                  ? "bg-background text-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {t}
            </button>
          ))}
        </div>
        {tab === "metrics" && (
          <div className="p-5">
            <div className="grid grid-cols-[1fr_120px_120px_120px] gap-4 border-b border-hairline pb-2 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              <div>Metric</div>
              <div className="text-right">Observed</div>
              <div className="text-right">Paper</div>
              <div className="text-right">Δ</div>
            </div>
            {Object.keys(report.metrics ?? {}).length === 0 ? (
              <div className="py-6 text-center text-[13px] text-muted-foreground">
                No metrics reported.
              </div>
            ) : (
              Object.entries(report.metrics ?? {}).map(([k, v]) => {
                const p = report.paper_metrics?.[k];
                return (
                  <div
                    key={k}
                    className="grid grid-cols-[1fr_120px_120px_120px] gap-4 border-b border-hairline py-2.5 text-[13px]"
                  >
                    <div className="text-foreground/90">{k}</div>
                    <div className="text-right text-mono text-foreground">{v.toFixed(4)}</div>
                    <div className="text-right text-mono text-muted-foreground">
                      {p != null ? p.toFixed(4) : "—"}
                    </div>
                    <div className="text-right text-mono text-muted-foreground">
                      {p != null ? (v - p).toFixed(4) : "—"}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
        {tab === "stdout" && (
          <pre className="max-h-[380px] overflow-auto p-4 text-mono text-[11px] text-foreground/80">
            {report.stdout ?? "No stdout captured."}
          </pre>
        )}
        {tab === "stderr" && (
          <pre className="max-h-[380px] overflow-auto p-4 text-mono text-[11px] text-[color:var(--danger)]/90">
            {report.stderr ?? "No stderr captured."}
          </pre>
        )}
      </div>

      {report.assumptions && report.assumptions.length > 0 && (
        <div className="mt-6 panel p-5">
          <div className="label-eyebrow mb-2">Run assumptions</div>
          <ul className="list-disc space-y-1 pl-4 text-[13px] text-muted-foreground">
            {report.assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

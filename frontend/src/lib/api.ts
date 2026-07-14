// ATLASS backend adapter. Presentation code only consumes these normalized contracts.

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, public body: unknown, message: string) {
    super(message);
  }
}

type Json = Record<string, unknown> | unknown[] | string | number | boolean | null;
export type ID = string;
export type PaperStatus = "uploaded" | "processing" | "ocr" | "extracting_text" | "creating_embeddings" | "ready" | "failed";

async function request<T>(path: string, options: RequestInit & { json?: Json; query?: Record<string, string | number | undefined | null> } = {}): Promise<T> {
  const { json, query, headers, ...init } = options;
  const params = new URLSearchParams();
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  });
  const url = `${BASE_URL}${path}${params.size ? `?${params}` : ""}`;
  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers: { Accept: "application/json", ...(json !== undefined ? { "Content-Type": "application/json" } : {}), ...(headers ?? {}) },
      body: json === undefined ? init.body : JSON.stringify(json),
    });
  } catch {
    throw new ApiError(0, null, `Unable to reach ATLASS backend at ${BASE_URL}`);
  }
  const text = await response.text();
  let body: any = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = text; }
  if (!response.ok) throw new ApiError(response.status, body, body?.detail || response.statusText || "Request failed");
  return body as T;
}

export interface AuthResponse { user: { id: ID; email?: string; name?: string } }
export interface Paper { id: ID; title: string; source_type?: string; source_ref?: string; status?: PaperStatus; created_at?: string; is_demo?: boolean }
export interface DashboardData { counts: { papers: number; ready: number; processing: number; projects: number; knowledge: number }; recent_papers?: Paper[]; continue?: { paper_id: ID; title: string; stage: string }[] }
export interface EventRecord { id?: ID; stage: string; message?: string; status?: "pending" | "running" | "done" | "failed"; at?: string }
export interface EvidenceCitation { section?: string; chunk?: string; score?: number }
export interface AskAnswer { answer: string; citations: EvidenceCitation[]; confidence?: number; sections: string[]; assumptions?: string[]; debug?: unknown }
export interface KnowledgeItem { kind: "concept" | "entity" | "relation" | string; label: string; frequency?: number; sections?: string[]; score?: number; paper_id?: ID; paper_title?: string }
export interface SpecField { value?: string | string[] | Record<string, unknown>; confidence?: number; citations?: EvidenceCitation[]; assumption?: boolean; status?: string }
export interface SystemSpec { fields: Record<string, SpecField>; approved?: boolean; updated_at?: string; version?: number }
export interface BlueprintModule { path: string; responsibility: string; assumption?: boolean; citations?: EvidenceCitation[] }
export interface Blueprint { modules: BlueprintModule[]; training_plan?: string; data_contracts?: unknown; dependencies?: string[]; config_schema?: unknown; assumptions?: string[]; approved?: boolean }
export interface BaselineProject { file_tree?: string[]; run_command?: string; supported_families?: string[]; warnings?: string[]; manifest?: Record<string, unknown>; source_mapping?: Record<string, string[]> }
export interface RunReport { status: "queued" | "running" | "succeeded" | "failed" | "not_run"; metrics?: Record<string, number>; stdout?: string; stderr?: string; assumptions?: string[]; comparability?: "comparable" | "not_comparable" | "unknown"; verdict?: string }
export interface CompareResult { aspect: string; papers: { paper_id: ID; title?: string; summary: string; citations?: EvidenceCitation[] }[]; synthesis?: string }

const citations = (evidence: any[] = []): EvidenceCitation[] => evidence.map((item) => ({ section: item.section, chunk: item.chunk_id == null ? undefined : `chunk ${item.chunk_id}`, score: item.score }));
const paper = (item: any): Paper => ({ ...item, is_demo: item.source_type === "demo" || Boolean(item.metadata?.demo_fixture) });
const status = (value: string): EventRecord["status"] => value === "ready" ? "done" : value === "failed" ? "failed" : value === "uploaded" ? "pending" : "running";

const systemSpec = (spec: any): SystemSpec => ({
  ...spec,
  approved: spec.review?.status === "approved",
  updated_at: spec.review?.updated_at ?? spec.generated_at,
  version: spec.review?.version,
  fields: Object.fromEntries(Object.entries(spec.fields ?? {}).map(([name, field]: [string, any]) => [name, { ...field, citations: citations(field.evidence), assumption: Boolean(field.assumption) }])),
});

const blueprint = (item: any): Blueprint => ({
  ...item,
  approved: item.review?.status === "approved",
  modules: (item.modules ?? []).map((module: any) => ({ ...module, citations: (module.evidence_fields ?? []).flatMap((field: string) => citations(item.evidence_map?.[field]?.evidence)) })),
  training_plan: Array.isArray(item.training_plan) ? item.training_plan.map((step: any) => `${step.step}: ${step.detail ?? "Needs review"}`).join("\n") : item.training_plan,
  dependencies: (item.dependencies ?? []).map((dependency: any) => typeof dependency === "string" ? dependency : dependency.package),
  assumptions: (item.assumptions ?? []).map((assumption: any) => typeof assumption === "string" ? assumption : assumption.description),
});

const baseline = (manifest: any): BaselineProject => ({
  manifest,
  file_tree: ["README.md", "requirements.txt", "config/experiment.json", ...Object.keys(manifest.source_mapping ?? {})],
  run_command: manifest.smoke_command ?? manifest.entrypoint,
  supported_families: ["pytorch_supervised_model"],
  warnings: manifest.scope ? [manifest.scope] : [],
  source_mapping: manifest.source_mapping,
});

const report = (item: any): RunReport => ({
  ...item,
  status: item.status === "completed" ? "succeeded" : item.status === "failed" ? "failed" : "not_run",
  metrics: item.observed_metrics ?? {},
  stdout: item.commands?.train?.stdout,
  stderr: item.commands?.train?.stderr || item.commands?.evaluate?.stderr,
  assumptions: (item.assumptions ?? []).map((assumption: any) => typeof assumption === "string" ? assumption : assumption.description),
  comparability: item.comparison?.status,
  verdict: item.comparison?.reason,
});

export const api = {
  base: BASE_URL,
  auth: {
    oauth: async (): Promise<AuthResponse> => ({ user: await request<any>("/auth/oauth", { method: "POST", json: { provider: "demo", subject: "student-demo", email: "student@atlass.local", name: "Student" } }) }),
  },
  dashboard: async (userId: ID): Promise<DashboardData> => {
    const item = await request<any>(`/users/${userId}/dashboard`);
    return { counts: { papers: item.papers ?? 0, ready: item.ready_papers ?? 0, processing: item.processing_papers ?? 0, projects: item.projects ?? 0, knowledge: item.memories ?? 0 } };
  },
  papers: {
    list: (userId: ID): Promise<Paper[]> => request<any[]>(`/users/${userId}/papers`).then((items) => items.map(paper)),
    create: (userId: ID, body: { source_type: "arxiv" | "doi" | "pdf"; source_ref: string; title?: string }): Promise<Paper> => request<any>(`/users/${userId}/papers`, { method: "POST", json: body }).then(paper),
    upload: async (userId: ID, file: File): Promise<Paper> => {
      const form = new FormData(); form.append("file", file);
      const response = await fetch(`${BASE_URL}/users/${userId}/papers/upload`, { method: "POST", body: form });
      if (!response.ok) throw new ApiError(response.status, null, await response.text());
      return paper(await response.json());
    },
    demo: (userId: ID): Promise<Paper> => request<any>(`/users/${userId}/demo-paper`, { method: "POST" }).then(paper),
    events: async (userId: ID, paperId: ID): Promise<EventRecord[]> => (await request<any[]>(`/users/${userId}/papers/${paperId}/events`)).map((item) => ({ id: item.id, stage: item.status, message: item.message, status: status(item.status), at: item.created_at })),
    ask: (userId: ID, paperId: ID, question: string, include_debug = false): Promise<AskAnswer> => request<any>(`/users/${userId}/papers/${paperId}/ask`, { method: "POST", json: { question, include_debug } }).then((item) => ({ ...item, citations: citations(item.provenance), sections: [...new Set((item.provenance ?? []).map((e: any) => e.section).filter(Boolean))], debug: item.retrieval_debug })),
    knowledge: async (userId: ID, paperId: ID): Promise<KnowledgeItem[]> => {
      const artifact = await request<any>(`/users/${userId}/papers/${paperId}/knowledge`);
      return ["concepts", "entities", "relations"].flatMap((collection) => (artifact[collection] ?? []).map((item: any) => ({ ...item, kind: collection === "concepts" ? "concept" : collection === "entities" ? "entity" : "relation", label: item.label ?? [item.source, item.relation, item.target].filter(Boolean).join(" "), frequency: item.frequency ?? item.evidence_count })));
    },
    promoteKnowledge: (userId: ID, paperId: ID, body: Json) => request(`/users/${userId}/papers/${paperId}/knowledge/promote`, { method: "POST", json: body }),
    compare: (userId: ID, body: { paper_ids: ID[]; aspect: string; include_debug?: boolean }): Promise<CompareResult> => request<any>(`/users/${userId}/papers/compare`, { method: "POST", json: body }).then((item) => ({ aspect: item.aspect, synthesis: item.synthesis, papers: Object.entries(item.comparisons ?? {}).map(([paper_id, comparison]: [string, any]) => ({ paper_id, title: comparison.paper_title, summary: comparison.answer, citations: citations(comparison.provenance) })) })),
  },
  knowledge: {
    search: (userId: ID, q?: string, kind?: string, paper_id?: ID, limit?: number): Promise<KnowledgeItem[]> => request<any>(`/users/${userId}/knowledge`, { query: { q, kind, paper_id, limit } }).then((item) => item.results ?? []),
  },
  spec: {
    generate: (userId: ID, paperId: ID): Promise<SystemSpec> => request<any>(`/users/${userId}/papers/${paperId}/system-spec`, { method: "POST" }).then(systemSpec),
    get: (userId: ID, paperId: ID): Promise<SystemSpec> => request<any>(`/users/${userId}/papers/${paperId}/system-spec`).then(systemSpec),
    patch: (userId: ID, paperId: ID, body: { field_updates?: Record<string, unknown>; notes?: string; approve?: boolean }): Promise<SystemSpec> => request<any>(`/users/${userId}/papers/${paperId}/system-spec`, { method: "PATCH", json: body }).then(systemSpec),
  },
  blueprint: {
    generate: (userId: ID, paperId: ID): Promise<Blueprint> => request<any>(`/users/${userId}/papers/${paperId}/implementation-blueprint`, { method: "POST" }).then(blueprint),
    get: (userId: ID, paperId: ID): Promise<Blueprint> => request<any>(`/users/${userId}/papers/${paperId}/implementation-blueprint`).then(blueprint),
    patch: (userId: ID, paperId: ID, body: { module_updates?: Record<string, string>; assumptions?: unknown[]; notes?: string; approve?: boolean }): Promise<Blueprint> => request<any>(`/users/${userId}/papers/${paperId}/implementation-blueprint`, { method: "PATCH", json: body }).then(blueprint),
  },
  baseline: {
    generate: (userId: ID, paperId: ID): Promise<BaselineProject> => request<any>(`/users/${userId}/papers/${paperId}/baseline-project`, { method: "POST" }).then(baseline),
    get: (userId: ID, paperId: ID): Promise<BaselineProject> => request<any>(`/users/${userId}/papers/${paperId}/baseline-project`).then(baseline),
    run: (userId: ID, paperId: ID): Promise<RunReport> => request<any>(`/users/${userId}/papers/${paperId}/baseline-project/run`, { method: "POST" }).then(report),
    report: (userId: ID, paperId: ID): Promise<RunReport> => request<any>(`/users/${userId}/papers/${paperId}/reproduction-report`).then(report),
  },
  projects: {
    list: (userId: ID) => request<any[]>(`/users/${userId}/projects`),
    create: (userId: ID, body: { name: string; description?: string }) => request(`/users/${userId}/projects`, { method: "POST", json: body }),
    addPaper: (userId: ID, projectId: ID, body: { paper_id: ID }) => request(`/users/${userId}/projects/${projectId}/papers`, { method: "POST", json: { resource_id: body.paper_id } }),
    timeline: (userId: ID, projectId: ID) => request(`/users/${userId}/projects/${projectId}/timeline`),
  },
};

export const STAGES = [
  { id: "import", label: "Import", description: "Ingest paper source" },
  { id: "understand", label: "Understand", description: "Ground evidence" },
  { id: "spec", label: "System Spec", description: "Structured design" },
  { id: "blueprint", label: "Blueprint", description: "Implementation plan" },
  { id: "baseline", label: "Baseline", description: "Runnable PyTorch" },
  { id: "report", label: "Report", description: "Reproduction verdict" },
] as const;
export type StageId = (typeof STAGES)[number]["id"];

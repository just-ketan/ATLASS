import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, FileText, Sparkles, GitBranch, Beaker, ClipboardCheck } from "lucide-react";
import { STAGES } from "@/lib/api";

export const Route = createFileRoute("/")({
  component: Landing,
  head: () => ({
    meta: [
      { title: "ATLASS — Turn papers into working systems" },
      {
        name: "description",
        content:
          "ATLASS is an AI research cognition system: paper → grounded evidence → specification → blueprint → runnable PyTorch baseline → honest reproduction report.",
      },
    ],
  }),
});

function Landing() {
  return (
    <div className="relative min-h-dvh overflow-hidden bg-background text-foreground">
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0 grid-bg opacity-40" aria-hidden />
      <div
        className="pointer-events-none absolute -left-40 top-[-10%] size-[720px] rounded-full opacity-[0.14] blur-3xl"
        style={{ background: "radial-gradient(circle, var(--evidence) 0%, transparent 60%)" }}
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -right-40 top-[30%] size-[720px] rounded-full opacity-[0.08] blur-3xl"
        style={{ background: "radial-gradient(circle, var(--info) 0%, transparent 60%)" }}
        aria-hidden
      />

      <header className="relative z-10 mx-auto flex max-w-[1200px] items-center justify-between px-6 py-6 sm:px-10">
        <div className="flex items-center gap-2.5">
          <span className="relative inline-flex size-8 items-center justify-center rounded-md border border-hairline-strong bg-surface">
            <span className="absolute inset-[3px] rounded-[3px] bg-linear-to-br from-[color:var(--evidence)]/60 to-transparent" />
            <span className="relative text-mono text-[11px] font-semibold text-foreground">Λ</span>
          </span>
          <div className="leading-none">
            <div className="text-[14px] font-semibold tracking-[0.02em]">ATLASS</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-subtle">
              Research cognition system
            </div>
          </div>
        </div>
        <nav className="hidden items-center gap-8 text-[13px] text-muted-foreground sm:flex">
          <a href="#workflow" className="hover:text-foreground">
            Workflow
          </a>
          <a href="#evidence" className="hover:text-foreground">
            Evidence
          </a>
          <a href="#principles" className="hover:text-foreground">
            Principles
          </a>
        </nav>
        <Link
          to="/app"
          className="inline-flex h-9 items-center gap-1.5 rounded-md bg-primary px-4 text-[13px] font-medium text-primary-foreground transition hover:opacity-90"
        >
          Open workspace <ArrowRight className="size-3.5" />
        </Link>
      </header>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-[1200px] px-6 pt-16 sm:px-10 sm:pt-28">
        <div className="mx-auto max-w-3xl text-center">
          <div className="label-eyebrow inline-flex items-center gap-2">
            <span className="size-1.5 rounded-full bg-[color:var(--evidence)]" />
            v0.4 · Evidence-first release
          </div>
          <h1 className="mt-6 text-display text-5xl leading-[1.02] tracking-tight sm:text-[68px]">
            Turn papers into working systems.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-[17px] leading-relaxed text-muted-foreground">
            Evidence-grounded understanding, implementation planning, and reproducible baselines —
            for researchers who need to move from PDF to PyTorch without losing the citation trail.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/app"
              className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-[14px] font-medium text-primary-foreground transition hover:opacity-90"
            >
              Open research workspace <ArrowRight className="size-4" />
            </Link>
            <a
              href="#workflow"
              className="inline-flex h-11 items-center gap-2 rounded-md border border-hairline-strong bg-surface px-5 text-[14px] font-medium text-foreground transition hover:bg-surface-2"
            >
              See the workflow
            </a>
          </div>
          <div className="mt-6 text-[12px] text-subtle">
            No account required · Load a synthetic demo paper in one click
          </div>
        </div>

        {/* Terminal-style preview */}
        <div className="relative mx-auto mt-20 max-w-[1080px]">
          <div className="rounded-2xl border border-hairline-strong bg-surface p-2 shadow-[var(--shadow-panel)]">
            <div className="flex items-center justify-between border-b border-hairline px-3 py-2">
              <div className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full bg-surface-3" />
                <span className="size-2.5 rounded-full bg-surface-3" />
                <span className="size-2.5 rounded-full bg-surface-3" />
              </div>
              <span className="text-mono text-[11px] text-muted-foreground">
                atlass · workspace / attention-is-all-you-need.pdf
              </span>
              <span className="text-[10px] uppercase tracking-[0.14em] text-[color:var(--evidence)]">
                evidence · 0.94
              </span>
            </div>
            <div className="grid grid-cols-1 gap-2 p-2 lg:grid-cols-[220px_1fr_260px]">
              <div className="hairline rounded-lg bg-background p-3">
                <div className="label-eyebrow">Stages</div>
                <ul className="mt-3 space-y-1.5 text-[12px]">
                  {STAGES.map((s, i) => (
                    <li key={s.id} className="flex items-center gap-2">
                      <span
                        className={
                          i < 3
                            ? "size-1.5 rounded-full bg-[color:var(--evidence)]"
                            : i === 3
                              ? "size-1.5 animate-pulse-soft rounded-full bg-[color:var(--evidence)] ring-2 ring-[color:var(--evidence-soft)]"
                              : "size-1.5 rounded-full bg-hairline-strong"
                        }
                      />
                      <span className={i <= 3 ? "text-foreground" : "text-muted-foreground"}>
                        {s.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="hairline rounded-lg bg-background p-4">
                <div className="label-eyebrow">System specification · draft</div>
                <div className="mt-3 text-display text-2xl">
                  Multi-head self-attention over token embeddings
                </div>
                <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                  The proposed system replaces recurrence with scaled dot-product attention across
                  parallel heads. Positional information is injected via sinusoidal encodings…
                </p>
                <div className="mt-4 flex flex-wrap gap-2 text-[11px]">
                  <span className="rounded-full border border-[color:var(--evidence)]/25 bg-[color:var(--evidence-soft)] px-2 py-0.5 text-[color:var(--evidence)]">
                    Supported · §3.2
                  </span>
                  <span className="rounded-full border border-hairline-strong bg-surface-2 px-2 py-0.5 text-muted-foreground">
                    Confidence 0.91
                  </span>
                  <span className="rounded-full border border-[color:var(--warning)]/30 bg-[color:var(--warning-soft)] px-2 py-0.5 text-[color:var(--warning)]">
                    1 assumption
                  </span>
                </div>
              </div>
              <div className="hairline rounded-lg bg-background p-3">
                <div className="label-eyebrow">Evidence</div>
                <div className="mt-3 space-y-2">
                  {[
                    { s: "3.2", t: "…attention function can be described as mapping a query and a set of key-value pairs…", sc: 0.92 },
                    { s: "5.3", t: "…we employed label smoothing of value ε_ls = 0.1…", sc: 0.78 },
                  ].map((c, i) => (
                    <div key={i} className="rounded-md border border-hairline p-2">
                      <div className="flex justify-between text-mono text-[10px]">
                        <span className="text-[color:var(--evidence)]">§{c.s}</span>
                        <span className="text-muted-foreground">score {c.sc}</span>
                      </div>
                      <p className="mt-1 line-clamp-3 text-[11px] leading-relaxed text-muted-foreground">
                        “{c.t}”
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div
            className="pointer-events-none absolute -inset-x-16 -bottom-16 h-40 opacity-40 blur-3xl"
            style={{ background: "radial-gradient(ellipse at center, var(--evidence) 0%, transparent 70%)" }}
            aria-hidden
          />
        </div>
      </section>

      {/* Workflow */}
      <section id="workflow" className="relative z-10 mx-auto mt-40 max-w-[1200px] px-6 sm:px-10">
        <div className="grid gap-10 lg:grid-cols-[380px_1fr]">
          <div>
            <div className="label-eyebrow">The workflow</div>
            <h2 className="mt-3 text-display text-4xl">
              Six deliberate stages. No opaque leaps.
            </h2>
            <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground">
              ATLASS never fabricates a reproduction. Every stage produces artifacts you can
              inspect, edit, and approve — and every claim carries its provenance forward.
            </p>
          </div>
          <ol className="space-y-2">
            {[
              { n: "01", t: "Import", d: "Ingest a paper via arXiv, DOI, or PDF upload. Parse, chunk, embed.", i: FileText },
              { n: "02", t: "Understand", d: "Ask questions. Every answer cites sections and shows confidence.", i: Sparkles },
              { n: "03", t: "System Specification", d: "Structured, editable design document with inline evidence.", i: ClipboardCheck },
              { n: "04", t: "Implementation Blueprint", d: "Modules, contracts, and training plan traceable back to sections.", i: GitBranch },
              { n: "05", t: "Runnable Baseline", d: "Constrained PyTorch project with a smoke experiment. Not a full reproduction.", i: Beaker },
              { n: "06", t: "Reproduction Report", d: "Observed metrics, paper metrics, and an honest comparability verdict.", i: ClipboardCheck },
            ].map((s, i) => {
              const Icon = s.i;
              return (
                <li
                  key={s.n}
                  className="group grid grid-cols-[64px_36px_1fr] items-start gap-4 rounded-lg border border-hairline bg-surface/60 p-4 transition hover:bg-surface-2/70"
                >
                  <span className="text-mono text-[13px] text-subtle">{s.n}</span>
                  <span className="mt-0.5 flex size-9 items-center justify-center rounded-md border border-hairline bg-background text-muted-foreground transition group-hover:text-[color:var(--evidence)]">
                    <Icon className="size-4" />
                  </span>
                  <div className="min-w-0">
                    <div className="text-[15px] font-medium text-foreground">{s.t}</div>
                    <div className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
                      {s.d}
                    </div>
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      {/* Principles */}
      <section id="principles" className="relative z-10 mx-auto mt-40 max-w-[1200px] px-6 sm:px-10">
        <div className="label-eyebrow">Principles</div>
        <h2 className="mt-3 max-w-2xl text-display text-4xl">
          Evidence over eloquence. Assumptions over hallucinations.
        </h2>
        <div className="mt-10 grid gap-px overflow-hidden rounded-xl border border-hairline bg-hairline-strong sm:grid-cols-3">
          {[
            {
              t: "Every claim shows its source.",
              d: "Answers, spec fields, and modules link back to the exact retrieved section and confidence score.",
            },
            {
              t: "Assumptions are labeled, not hidden.",
              d: "When the paper is silent, ATLASS flags the gap and asks for your judgment before proceeding.",
            },
            {
              t: "Baselines admit their scope.",
              d: "Synthetic smoke runs are labeled non-comparable. We refuse to imply a reproduction we can't defend.",
            },
          ].map((p) => (
            <div key={p.t} className="bg-background p-6">
              <div className="text-display text-xl leading-snug text-foreground">{p.t}</div>
              <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">{p.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section id="evidence" className="relative z-10 mx-auto my-40 max-w-[1200px] px-6 sm:px-10">
        <div className="relative overflow-hidden rounded-2xl border border-hairline-strong bg-surface p-10 text-center sm:p-16">
          <div className="pointer-events-none absolute inset-0 grid-bg opacity-40" aria-hidden />
          <div className="relative">
            <h3 className="text-display text-4xl leading-tight sm:text-5xl">
              Ready to move from paper to system?
            </h3>
            <p className="mx-auto mt-5 max-w-xl text-[15px] text-muted-foreground">
              Load a synthetic fixture, or bring your own arXiv paper. The workspace opens with
              every stage wired end-to-end.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/app"
                className="inline-flex h-11 items-center gap-2 rounded-md bg-primary px-5 text-[14px] font-medium text-primary-foreground transition hover:opacity-90"
              >
                Open research workspace <ArrowRight className="size-4" />
              </Link>
              <Link
                to="/app/library"
                className="inline-flex h-11 items-center gap-2 rounded-md border border-hairline-strong bg-background px-5 text-[14px] font-medium text-foreground transition hover:bg-surface-2"
              >
                Browse library
              </Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="relative z-10 hairline-t mt-10">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-8 text-[12px] text-subtle sm:px-10">
          <div>© {new Date().getFullYear()} ATLASS · Research cognition system</div>
          <div className="text-mono">v0.4 · build 2024.11</div>
        </div>
      </footer>
    </div>
  );
}

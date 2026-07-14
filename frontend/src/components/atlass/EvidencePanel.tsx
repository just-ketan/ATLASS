import { clsx } from "clsx";
import type { EvidenceCitation } from "@/lib/api";
import { FileText } from "lucide-react";

export function EvidencePanel({
  title = "Evidence",
  citations = [],
  confidence,
  sections = [],
  assumptions = [],
  empty,
  className,
}: {
  title?: string;
  citations?: EvidenceCitation[];
  confidence?: number;
  sections?: string[];
  assumptions?: string[];
  empty?: string;
  className?: string;
}) {
  const hasAny =
    citations.length > 0 || sections.length > 0 || assumptions.length > 0 || confidence != null;
  return (
    <div className={clsx("space-y-5", className)}>
      <div>
        <div className="label-eyebrow">{title}</div>
        {confidence != null && <ConfidenceBar value={confidence} className="mt-3" />}
      </div>

      {sections.length > 0 && (
        <div>
          <div className="label-eyebrow mb-2 text-[10px]">Retrieved sections</div>
          <ul className="space-y-1">
            {sections.map((s, i) => (
              <li
                key={i}
                className="flex items-center gap-2 rounded-md border border-hairline bg-surface px-2.5 py-1.5 text-[12px] text-foreground/85"
              >
                <FileText className="size-3 text-muted-foreground" />
                <span className="truncate">{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {citations.length > 0 && (
        <div>
          <div className="label-eyebrow mb-2 text-[10px]">Citations</div>
          <ul className="space-y-2">
            {citations.map((c, i) => (
              <li
                key={i}
                className="rounded-md border border-hairline bg-surface p-2.5"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-mono text-[11px] text-[color:var(--evidence)]">
                    §{c.section ?? "?"}
                    {c.page != null && ` · p.${c.page}`}
                  </span>
                  {c.score != null && (
                    <span className="text-mono text-[10px] text-muted-foreground">
                      score {c.score.toFixed(2)}
                    </span>
                  )}
                </div>
                {c.chunk && (
                  <p className="mt-1.5 line-clamp-4 text-[12px] leading-relaxed text-muted-foreground">
                    “{c.chunk}”
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {assumptions.length > 0 && (
        <div>
          <div className="label-eyebrow mb-2 text-[10px] text-[color:var(--warning)]">
            Assumptions
          </div>
          <ul className="space-y-1.5">
            {assumptions.map((a, i) => (
              <li
                key={i}
                className="rounded-md border border-[color:var(--warning)]/25 bg-[color:var(--warning-soft)]/60 px-2.5 py-1.5 text-[12px] text-foreground/90"
              >
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!hasAny && (
        <div className="rounded-md border border-hairline border-dashed bg-surface/50 p-4 text-center text-[12px] text-muted-foreground">
          {empty ?? "No evidence has been grounded yet."}
        </div>
      )}
    </div>
  );
}

export function ConfidenceBar({ value, className }: { value: number; className?: string }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  const color =
    pct >= 75
      ? "var(--evidence)"
      : pct >= 45
        ? "var(--confidence)"
        : "var(--warning)";
  return (
    <div className={clsx("space-y-1.5", className)}>
      <div className="flex items-baseline justify-between text-[11px] text-muted-foreground">
        <span className="uppercase tracking-[0.14em]">Confidence</span>
        <span className="text-mono text-foreground">{pct}%</span>
      </div>
      <div className="h-1 w-full overflow-hidden rounded-full bg-surface-2">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

import { clsx } from "clsx";
import { Check } from "lucide-react";
import { STAGES, type StageId } from "@/lib/api";

export function WorkflowTimeline({
  current,
  completed = [],
  onSelect,
  compact = false,
}: {
  current?: StageId;
  completed?: StageId[];
  onSelect?: (id: StageId) => void;
  compact?: boolean;
}) {
  const currentIdx = STAGES.findIndex((s) => s.id === current);
  return (
    <ol className={clsx("relative flex w-full", compact ? "gap-0" : "gap-0")}>
      {STAGES.map((stage, idx) => {
        const isDone = completed.includes(stage.id) || (currentIdx >= 0 && idx < currentIdx);
        const isCurrent = current === stage.id;
        const isFuture = !isDone && !isCurrent;
        return (
          <li key={stage.id} className="flex min-w-0 flex-1 items-start">
            <button
              type="button"
              onClick={() => onSelect?.(stage.id)}
              className={clsx(
                "group relative flex w-full flex-col items-start gap-2 py-4 pr-4 text-left transition",
                onSelect && "cursor-pointer",
              )}
            >
              {/* Connector line */}
              {idx > 0 && (
                <span
                  className={clsx(
                    "absolute left-0 top-[26px] h-px w-full -translate-x-1/2",
                    isDone || isCurrent
                      ? "bg-[color:var(--evidence)]/50"
                      : "bg-hairline-strong",
                  )}
                  aria-hidden
                />
              )}
              {/* Node */}
              <span
                className={clsx(
                  "relative z-10 flex size-6 items-center justify-center rounded-full border transition",
                  isDone &&
                    "border-[color:var(--evidence)]/60 bg-[color:var(--evidence-soft)] text-[color:var(--evidence)]",
                  isCurrent &&
                    "border-[color:var(--evidence)] bg-background text-[color:var(--evidence)] shadow-[0_0_0_4px_var(--evidence-soft)]",
                  isFuture && "border-hairline-strong bg-surface text-muted-foreground",
                )}
              >
                {isDone ? (
                  <Check className="size-3" strokeWidth={2.5} />
                ) : (
                  <span className="text-mono text-[10px]">{idx + 1}</span>
                )}
                {isCurrent && (
                  <span className="absolute inset-0 animate-pulse-soft rounded-full ring-1 ring-[color:var(--evidence)]/40" />
                )}
              </span>
              {!compact && (
                <div className="min-w-0">
                  <div
                    className={clsx(
                      "truncate text-[13px] font-medium tracking-tight",
                      isCurrent
                        ? "text-foreground"
                        : isDone
                          ? "text-foreground/80"
                          : "text-muted-foreground",
                    )}
                  >
                    {stage.label}
                  </div>
                  <div className="mt-0.5 truncate text-[11px] text-subtle">
                    {stage.description}
                  </div>
                </div>
              )}
            </button>
          </li>
        );
      })}
    </ol>
  );
}

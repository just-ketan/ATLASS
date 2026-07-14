import { clsx } from "clsx";
import type { ReactNode } from "react";

type Variant = "neutral" | "evidence" | "confidence" | "warning" | "danger" | "info" | "muted";

const styles: Record<Variant, string> = {
  neutral:
    "bg-surface-2 text-foreground/85 border-hairline-strong",
  evidence:
    "bg-[color:var(--evidence-soft)] text-[color:var(--evidence)] border-[color:var(--evidence)]/25",
  confidence:
    "bg-[color:var(--evidence-soft)] text-[color:var(--confidence)] border-[color:var(--confidence)]/25",
  warning:
    "bg-[color:var(--warning-soft)] text-[color:var(--warning)] border-[color:var(--warning)]/30",
  danger:
    "bg-[color:var(--danger-soft)] text-[color:var(--danger)] border-[color:var(--danger)]/30",
  info: "bg-[color:var(--info)]/10 text-[color:var(--info)] border-[color:var(--info)]/25",
  muted: "bg-surface text-muted-foreground border-hairline",
};

export function StatusChip({
  variant = "neutral",
  children,
  dot = true,
  className,
}: {
  variant?: Variant;
  children: ReactNode;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-[3px] text-[11px] font-medium tracking-wide",
        styles[variant],
        className,
      )}
    >
      {dot && (
        <span
          className={clsx(
            "size-1.5 rounded-full",
            variant === "evidence" || variant === "confidence"
              ? "bg-[color:var(--evidence)]"
              : variant === "warning"
                ? "bg-[color:var(--warning)]"
                : variant === "danger"
                  ? "bg-[color:var(--danger)]"
                  : variant === "info"
                    ? "bg-[color:var(--info)]"
                    : "bg-muted-foreground/60",
            variant === "warning" || variant === "danger" ? "" : "animate-pulse-soft",
          )}
        />
      )}
      {children}
    </span>
  );
}

export function statusToVariant(status?: string): Variant {
  switch (status) {
    case "ready":
    case "done":
    case "succeeded":
    case "supported":
    case "comparable":
      return "evidence";
    case "processing":
    case "extracting_text":
    case "creating_embeddings":
    case "running":
    case "queued":
      return "info";
    case "assumption":
    case "user_edited":
    case "not_comparable":
      return "warning";
    case "failed":
    case "missing":
      return "danger";
    default:
      return "neutral";
  }
}

export function humanStatus(status?: string) {
  if (!status) return "Unknown";
  return status
    .split("_")
    .map((s) => s[0]?.toUpperCase() + s.slice(1))
    .join(" ");
}

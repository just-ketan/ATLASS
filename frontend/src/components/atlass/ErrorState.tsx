import { clsx } from "clsx";
import type { ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

export function ErrorState({
  title = "Backend unavailable",
  description,
  onRetry,
  className,
}: {
  title?: string;
  description?: ReactNode;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "panel flex items-start gap-4 border-[color:var(--warning)]/30 bg-[color:var(--warning-soft)]/50 p-5",
        className,
      )}
    >
      <div className="mt-0.5 shrink-0 rounded-md border border-[color:var(--warning)]/30 bg-[color:var(--warning-soft)] p-2 text-[color:var(--warning)]">
        <AlertTriangle className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[14px] font-medium text-foreground">{title}</div>
        {description && (
          <div className="mt-1 text-[13px] leading-relaxed text-muted-foreground">
            {description}
          </div>
        )}
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 inline-flex h-8 items-center gap-1.5 rounded-md border border-hairline-strong bg-surface-2 px-3 text-[12px] font-medium text-foreground transition hover:bg-surface-3"
          >
            <RefreshCw className="size-3.5" /> Retry
          </button>
        )}
      </div>
    </div>
  );
}

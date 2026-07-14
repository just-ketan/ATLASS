import { clsx } from "clsx";
import { useState } from "react";
import { ChevronRight, Braces } from "lucide-react";

export function JsonInspector({
  data,
  label = "Raw JSON",
  defaultOpen = false,
  className,
}: {
  data: unknown;
  label?: string;
  defaultOpen?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={clsx("rounded-lg border border-hairline bg-surface", className)}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        <ChevronRight
          className={clsx("size-3.5 text-muted-foreground transition-transform", open && "rotate-90")}
        />
        <Braces className="size-3.5 text-muted-foreground" />
        <span className="text-[12px] font-medium text-foreground/85">{label}</span>
        <span className="ml-auto text-[10px] uppercase tracking-[0.14em] text-subtle">
          Inspect
        </span>
      </button>
      {open && (
        <pre className="max-h-[420px] overflow-auto border-t border-hairline bg-background/50 p-3 font-mono text-[11px] leading-relaxed text-foreground/80">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

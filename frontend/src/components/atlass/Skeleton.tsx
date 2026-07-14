import { clsx } from "clsx";

export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx("skeleton", className)} />;
}

export function SkeletonBlock({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className={clsx("h-3", i === rows - 1 ? "w-2/3" : "w-full")} />
      ))}
    </div>
  );
}

export function PipelineLoading({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 text-[13px] text-muted-foreground">
      <span className="relative flex size-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[color:var(--evidence)] opacity-60" />
        <span className="relative inline-flex size-2 rounded-full bg-[color:var(--evidence)]" />
      </span>
      <span className="text-mono text-[12px] tracking-tight text-foreground/80">{label}</span>
    </div>
  );
}

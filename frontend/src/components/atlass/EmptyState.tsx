import { clsx } from "clsx";
import type { ReactNode } from "react";

export function EmptyState({
  eyebrow,
  title,
  description,
  action,
  className,
  glyph = "grid",
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
  glyph?: "grid" | "spec" | "graph" | "flask" | "compare";
}) {
  return (
    <div
      className={clsx(
        "flex flex-col items-center justify-center px-6 py-16 text-center",
        className,
      )}
    >
      <Glyph kind={glyph} />
      {eyebrow && <div className="label-eyebrow mt-8">{eyebrow}</div>}
      <h3 className="mt-3 text-display text-2xl text-foreground">{title}</h3>
      {description && (
        <p className="mt-3 max-w-md text-[14px] leading-relaxed text-muted-foreground">
          {description}
        </p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

function Glyph({ kind }: { kind: "grid" | "spec" | "graph" | "flask" | "compare" }) {
  // Restrained geometric SVGs, hairline strokes.
  const common = {
    width: 88,
    height: 88,
    viewBox: "0 0 88 88",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1,
    className: "text-muted-foreground/50",
  };
  switch (kind) {
    case "spec":
      return (
        <svg {...common}>
          <rect x="16" y="10" width="56" height="68" rx="2" />
          <line x1="24" y1="24" x2="52" y2="24" />
          <line x1="24" y1="34" x2="64" y2="34" />
          <line x1="24" y1="44" x2="60" y2="44" />
          <line x1="24" y1="54" x2="56" y2="54" />
          <line x1="24" y1="64" x2="44" y2="64" />
          <circle cx="70" cy="24" r="2" className="text-[color:var(--evidence)]" />
        </svg>
      );
    case "graph":
      return (
        <svg {...common}>
          <circle cx="20" cy="24" r="5" />
          <circle cx="68" cy="18" r="5" />
          <circle cx="44" cy="44" r="5" />
          <circle cx="20" cy="66" r="5" />
          <circle cx="68" cy="64" r="5" />
          <line x1="24" y1="26" x2="40" y2="42" />
          <line x1="64" y1="20" x2="48" y2="42" />
          <line x1="44" y1="49" x2="24" y2="62" />
          <line x1="48" y1="46" x2="64" y2="62" />
        </svg>
      );
    case "flask":
      return (
        <svg {...common}>
          <path d="M34 12 L34 34 L20 66 A6 6 0 0 0 26 74 L62 74 A6 6 0 0 0 68 66 L54 34 L54 12" />
          <line x1="28" y1="12" x2="60" y2="12" />
          <line x1="26" y1="54" x2="62" y2="54" />
        </svg>
      );
    case "compare":
      return (
        <svg {...common}>
          <rect x="12" y="18" width="28" height="52" rx="2" />
          <rect x="48" y="18" width="28" height="52" rx="2" />
          <line x1="18" y1="30" x2="34" y2="30" />
          <line x1="18" y1="40" x2="34" y2="40" />
          <line x1="54" y1="30" x2="70" y2="30" />
          <line x1="54" y1="40" x2="70" y2="40" />
        </svg>
      );
    default:
      return (
        <svg {...common}>
          {[0, 1, 2, 3].map((r) =>
            [0, 1, 2, 3].map((c) => (
              <rect key={`${r}-${c}`} x={12 + c * 18} y={12 + r * 18} width="12" height="12" />
            )),
          )}
        </svg>
      );
  }
}

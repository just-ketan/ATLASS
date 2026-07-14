import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import {
  LayoutGrid,
  Library,
  GitCompareArrows,
  FolderKanban,
  Network,
  Activity,
  Search,
  Command,
  ShieldCheck,
  ChevronsUpDown,
  Sparkles,
} from "lucide-react";
import { clsx } from "clsx";
import { useEffect, useState, type ReactNode } from "react";
import { CommandPalette } from "./CommandPalette";

const NAV: { to: string; label: string; icon: typeof LayoutGrid; exact?: boolean }[] = [
  { to: "/app", label: "Overview", icon: LayoutGrid, exact: true },
  { to: "/app/library", label: "Library", icon: Library },
  { to: "/app/compare", label: "Compare", icon: GitCompareArrows },
  { to: "/app/projects", label: "Projects", icon: FolderKanban },
  { to: "/app/knowledge", label: "Knowledge", icon: Network },
  { to: "/app/activity", label: "Activity", icon: Activity },
];

export function AppShell({
  children,
  right,
  contextPaper,
}: {
  children: ReactNode;
  right?: ReactNode;
  contextPaper?: { id: string; title: string } | null;
}) {
  const [paletteOpen, setPaletteOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="min-h-dvh bg-background text-foreground">
      {/* Top bar */}
      <header className="sticky top-0 z-40 hairline-b glass">
        <div className="flex h-14 items-center gap-4 px-5">
          <Link to="/app" className="flex items-center gap-2.5">
            <LogoMark />
            <div className="hidden sm:flex flex-col leading-none">
              <span className="text-[13px] font-semibold tracking-[0.02em] text-foreground">
                ATLASS
              </span>
              <span className="text-[10px] uppercase tracking-[0.18em] text-subtle">
                Research OS
              </span>
            </div>
          </Link>

          <div className="mx-2 hidden h-6 w-px bg-hairline-strong sm:block" />

          {/* Paper switcher */}
          <button
            onClick={() => setPaletteOpen(true)}
            className="hidden max-w-[380px] items-center gap-2 rounded-md border border-hairline bg-surface px-2.5 py-1.5 text-left transition hover:bg-surface-2 md:flex"
          >
            <span className="label-eyebrow text-[10px]">Paper</span>
            <span className="truncate text-[13px] text-foreground">
              {contextPaper?.title ?? "No paper selected"}
            </span>
            <ChevronsUpDown className="size-3.5 shrink-0 text-muted-foreground" />
          </button>

          <div className="flex-1" />

          {/* Search trigger */}
          <button
            onClick={() => setPaletteOpen(true)}
            className="group flex h-9 min-w-0 items-center gap-2 rounded-md border border-hairline bg-surface pl-2.5 pr-1.5 text-[13px] text-muted-foreground transition hover:bg-surface-2 sm:min-w-[280px]"
          >
            <Search className="size-3.5" />
            <span className="hidden truncate sm:inline">Search papers, evidence, knowledge…</span>
            <span className="sm:hidden">Search</span>
            <span className="ml-auto hidden items-center gap-1 rounded border border-hairline bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:flex">
              <Command className="size-3" />K
            </span>
          </button>

          {/* Evidence integrity */}
          <div className="hidden items-center gap-2 rounded-md border border-hairline bg-surface px-2.5 py-1.5 lg:flex">
            <ShieldCheck className="size-3.5 text-[color:var(--evidence)]" />
            <div className="flex flex-col leading-none">
              <span className="text-[10px] uppercase tracking-[0.14em] text-subtle">Evidence</span>
              <span className="text-mono text-[11px] text-foreground">integrity · 0.94</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="sticky top-14 hidden h-[calc(100dvh-56px)] w-[220px] shrink-0 hairline-r md:block">
          <nav className="flex h-full flex-col px-3 py-5">
            <div className="label-eyebrow mb-2 px-2">Workspace</div>
            <ul className="space-y-0.5">
              {NAV.map((item) => {
                const active = item.exact
                  ? location.pathname === item.to
                  : location.pathname.startsWith(item.to);
                const Icon = item.icon;
                return (
                  <li key={item.to}>
                    <Link
                      to={item.to as any}
                      className={clsx(
                        "group flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-[13px] transition",
                        active
                          ? "bg-surface-2 text-foreground"
                          : "text-muted-foreground hover:bg-surface hover:text-foreground",
                      )}
                    >
                      <Icon
                        className={clsx(
                          "size-3.5",
                          active ? "text-[color:var(--evidence)]" : "text-muted-foreground",
                        )}
                      />
                      <span className="tracking-tight">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="mt-auto space-y-3">
              <div className="rounded-lg border border-hairline bg-surface p-3">
                <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <Sparkles className="size-3 text-[color:var(--evidence)]" />
                  Synthetic demo
                </div>
                <p className="mt-1.5 text-[12px] leading-relaxed text-muted-foreground">
                  Load a fixture to explore the full workflow without a real paper.
                </p>
                <button
                  onClick={() => navigate({ to: "/app/library" })}
                  className="mt-2 h-7 w-full rounded-md bg-primary text-[12px] font-medium text-primary-foreground hover:opacity-90"
                >
                  Load demo paper
                </button>
              </div>
              <div className="px-2 text-[10px] uppercase tracking-[0.14em] text-subtle">
                v0.4 · build 2024.11
              </div>
            </div>
          </nav>
        </aside>

        {/* Main */}
        <main className="min-w-0 flex-1">{children}</main>

        {right && (
          <aside className="sticky top-14 hidden h-[calc(100dvh-56px)] w-[360px] shrink-0 overflow-y-auto hairline-l xl:block">
            {right}
          </aside>
        )}
      </div>

      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  );
}

function LogoMark() {
  return (
    <span className="relative inline-flex size-7 items-center justify-center rounded-md border border-hairline-strong bg-surface">
      <span className="absolute inset-[3px] rounded-[3px] bg-linear-to-br from-[color:var(--evidence)]/70 to-transparent opacity-70" />
      <span className="relative text-mono text-[10px] font-semibold tracking-tighter text-foreground">
        Λ
      </span>
    </span>
  );
}

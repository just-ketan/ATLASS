import { Command } from "cmdk";
import {
  ArrowRight,
  Library,
  LayoutGrid,
  GitCompareArrows,
  FolderKanban,
  Network,
  Activity,
  FileText,
  Sparkles,
} from "lucide-react";
import { useNavigate } from "@tanstack/react-router";

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
}) {
  const navigate = useNavigate();
  if (!open) return null;

  const go = (to: string) => {
    onOpenChange(false);
    navigate({ to } as any);
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center px-4 pt-[10dvh]"
      onClick={() => onOpenChange(false)}
    >
      <div className="absolute inset-0 bg-background/70 backdrop-blur-md" />
      <div
        className="relative w-full max-w-[620px] overflow-hidden rounded-xl border border-hairline-strong bg-surface shadow-[var(--shadow-float)] animate-fade-up"
        onClick={(e) => e.stopPropagation()}
      >
        <Command label="ATLASS command palette" className="w-full">
          <div className="flex items-center gap-3 border-b border-hairline px-4 py-3">
            <Sparkles className="size-4 text-[color:var(--evidence)]" />
            <Command.Input
              placeholder="Type a command, search papers, or ask evidence…"
              className="w-full bg-transparent text-[14px] text-foreground placeholder:text-muted-foreground focus:outline-none"
              autoFocus
            />
            <span className="hidden items-center gap-1 rounded border border-hairline bg-surface-2 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground sm:flex">
              ESC
            </span>
          </div>
          <Command.List className="max-h-[420px] overflow-y-auto p-2">
            <Command.Empty className="px-3 py-8 text-center text-[13px] text-muted-foreground">
              No matches — try a different phrase.
            </Command.Empty>

            <Command.Group heading="Navigate" className="mb-2 [&_[cmdk-group-heading]]:label-eyebrow [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:pb-1.5 [&_[cmdk-group-heading]]:pt-2">
              <Item onSelect={() => go("/app")} icon={<LayoutGrid className="size-4" />} label="Overview" hint="Home" />
              <Item onSelect={() => go("/app/library")} icon={<Library className="size-4" />} label="Library" hint="All papers" />
              <Item onSelect={() => go("/app/compare")} icon={<GitCompareArrows className="size-4" />} label="Compare" hint="Multi-paper" />
              <Item onSelect={() => go("/app/projects")} icon={<FolderKanban className="size-4" />} label="Projects" hint="Research memory" />
              <Item onSelect={() => go("/app/knowledge")} icon={<Network className="size-4" />} label="Knowledge" hint="Concepts & entities" />
              <Item onSelect={() => go("/app/activity")} icon={<Activity className="size-4" />} label="Activity" hint="Recent events" />
            </Command.Group>

            <Command.Group heading="Actions" className="mb-2 [&_[cmdk-group-heading]]:label-eyebrow [&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:pb-1.5 [&_[cmdk-group-heading]]:pt-2">
              <Item onSelect={() => go("/app/library?action=demo")} icon={<Sparkles className="size-4" />} label="Load synthetic demo paper" hint="Workflow fixture" />
              <Item onSelect={() => go("/app/library?action=arxiv")} icon={<FileText className="size-4" />} label="Ingest from arXiv" hint="Paste an ID" />
            </Command.Group>
          </Command.List>
          <div className="hairline-t flex items-center justify-between px-3 py-2 text-[11px] text-subtle">
            <span>ATLASS · evidence-grounded navigation</span>
            <span className="text-mono">↩ select · ↑↓ move</span>
          </div>
        </Command>
      </div>
    </div>
  );
}

function Item({
  onSelect,
  icon,
  label,
  hint,
}: {
  onSelect: () => void;
  icon: React.ReactNode;
  label: string;
  hint?: string;
}) {
  return (
    <Command.Item
      onSelect={onSelect}
      className="group flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-[13px] text-foreground/85 aria-selected:bg-surface-2 aria-selected:text-foreground"
    >
      <span className="text-muted-foreground group-aria-selected:text-[color:var(--evidence)]">
        {icon}
      </span>
      <span className="flex-1 truncate">{label}</span>
      {hint && <span className="text-[11px] text-muted-foreground">{hint}</span>}
      <ArrowRight className="size-3.5 text-muted-foreground opacity-0 group-aria-selected:opacity-100" />
    </Command.Item>
  );
}
